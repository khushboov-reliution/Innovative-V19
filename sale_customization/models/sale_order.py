# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import _, api, fields, models
import io
import base64
from PyPDF2 import PdfFileMerger

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contact_person = fields.Many2one('res.partner', string='Contact Person', context={"from_dcr": True},
                                     domain="[('parent_id','=',partner_id)]")
    valid_upto = fields.Date(string='Valid Upto')
    validity_date = fields.Date(
        string="Expiration",
        help="Validity of the order..."
            )
    brand_id = fields.Many2one(
        'brand.master',
        string="Brand",
        domain="[('is_competitor','=', False)]"
    )

    packing_id = fields.Many2one('packing.details',string="Packing & Forwarding")
    insurance_id = fields.Many2one('insurance.details',string="Insurance")
    dispatch_through_id = fields.Many2one('dispatch.details',string="Dispatch Through")
    picking_policy_id = fields.Many2one('picking.policy',string="Picking Policy")
    enquiry_date = fields.Date(string="Enquiry Date")
    enquiry_number = fields.Char(string="Enquiry Number")

    @api.onchange('enquiry_date')
    def _onchange_enquiry_date(self):
        if self.enquiry_date and self.enquiry_date > fields.Date.today():
            self.enquiry_date = fields.Date.today()
            return {
                'warning': {
                    'title': _("Invalid Date Selection"),
                    'message': _("You cannot select a future date for an enquiry. The date has been reset to today."),
                }
            }

    dispatch_through = fields.Char(
        string="Dispatch Through",
        compute="_compute_dispatch_through",
        store=True
    )

    @api.depends('carrier_id')
    def _compute_dispatch_through(self):
        for order in self:
            order.dispatch_through = order.carrier_id.name if order.carrier_id else False


    @api.onchange('brand_id')
    def _onchange_brand_set_lines(self):
        """Update existing order lines when brand changes"""
        for order in self:
            for line in order.order_line:
                line.brand_id = order.brand_id.id if order.brand_id else False

    def _check_credit_limit(self):
        for order in self:
            partner = order.partner_id
            if not partner.credit_limit_amount:
                continue  # Skip check if no limit set

            # --- Get all unpaid invoices (posted + open/partial) ---
            unpaid_invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ])

            total_unpaid = sum(inv.amount_residual for inv in unpaid_invoices)
            total_with_order = total_unpaid + order.amount_total

            # --- Check limit ---
            if total_with_order > partner.credit_limit_amount:
                raise ValidationError(_(
                    "Credit limit exceeded for customer '%s'.\n"
                    "Credit Limit: %.2f\n"
                    "Unpaid Invoices Total: %.2f\n"
                    "Current Sale Order Total: %.2f\n"
                    "Total After Order: %.2f"
                ) % (partner.name, partner.credit_limit_amount, total_unpaid, order.amount_total, total_with_order))

    def action_confirm(self):
        self._check_credit_limit()
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    brand_id = fields.Many2one("brand.master", string="Brand")
    # application_type_id = fields.Many2one("application.type", string="Application",
    #                                       domain="[('brand_id','child_of',brand_id)]")

    brand_domain = fields.Char()

    last_sold_price = fields.Float(
        string="Last Sold Price",
        readonly=True,
        compute='_compute_last_sold_price',
        store=False
    )

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_last_sold_price(self):
        SaleOrderLine = self.env['sale.order.line']

        for line in self:
            line.last_sold_price = 0.0

            partner = line.order_id.partner_id
            product = line.product_id

            if not partner or not product:
                continue

            last_line = SaleOrderLine.search([
                ('order_partner_id', '=', partner.id),
                ('product_id', '=', product.id),
                ('state', 'in', ['sale', 'done']),
            ], order='create_date DESC', limit=1)

            if last_line:
                line.last_sold_price = last_line.price_unit
                line.price_unit = last_line.price_unit

    # @api.depends('brand_id', 'application_type_id')
    @api.onchange('brand_id')
    def _onchange_brand(self):
        for line in self:
            domain = []
            if line.brand_id:
                domain.append(('brand_id', '=', line.brand_id.id))
            # if line.application_type_id:
            #     domain.append(('application_type_id', '=', line.application_type_id.id))

            line.brand_domain = domain

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.brand_id = line.product_id.brand_id.id
                # line.application_type_id = line.product_id.application_type_id.id

    @api.onchange('order_id')
    def _onchange_order_set_default_brand(self):
        """Set default brand on new lines"""
        if self.order_id and self.order_id.brand_id:
            self.brand_id = self.order_id.brand_id.id

    @api.onchange('brand_id')
    def _onchange_brand_domain(self):
        """Apply domain → show only products of this brand."""
        for line in self:
            if line.brand_id:
                return {
                    'domain': {
                        'product_id': [
                            ('brand_id', '=', line.brand_id.id),
                            ('brand_id.is_competitor', '=', False)
                        ]
                    }
                }
        else:
            return {
                'domain': {
                    'product_id': [
                        ('brand_id.is_competitor', '=', False)
                    ]
                }
            }


class AccountMoveSendWizard(models.TransientModel):
    _inherit = 'account.move.send.wizard'

    mail_attachments_widget = fields.Json(
        compute='_compute_mail_attachments_widget',
        store=False,
        readonly=True,
    )

    @api.depends('template_id', 'invoice_edi_format', 'extra_edis', 'pdf_report_id')
    def _compute_mail_attachments_widget(self):
        """Prepare in-memory attachments for preview (no ID, no DB creation)."""
        for wizard in self:
            default_attachments = self._get_default_mail_attachments_widget(
                wizard.move_id,
                wizard.template_id,
                invoice_edi_format=wizard.invoice_edi_format,
                extra_edis=wizard.extra_edis or {},
                pdf_report=wizard.pdf_report_id,
            )

            custom_attachments = []
            invoice = wizard.move_id

            for line in invoice.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    for stock_move in sale_line.move_ids:
                        for move_line in stock_move.move_line_ids:
                            pdf_data = move_line.pdf_attachment
                            if not pdf_data:
                                continue

                            # Ensure pdf_data is a base64 string
                            if isinstance(pdf_data, bytes):
                                pdf_data = base64.b64encode(pdf_data).decode()
                            elif isinstance(pdf_data, str):
                                # assume already base64-encoded string
                                pass

                            filename = move_line.pdf_filename or f"{move_line.lot_id.name}.pdf"

                            custom_attachments.append({
                                "name": filename,
                                "mimetype": "application/pdf",
                                "datas": pdf_data,
                                "type": "binary",
                            })

            wizard.mail_attachments_widget = default_attachments + custom_attachments

    def action_send_and_print(self):
        """Create real ir.attachment for custom attachments before sending."""
        for wizard in self:
            invoice = wizard.move_id
            new_widget = []

            for att in (wizard.mail_attachments_widget or []):
                # if existing attachment (has id), keep as is
                if att.get("id"):
                    new_widget.append(att)
                    continue

                # if in-memory attachment (has datas), create ir.attachment
                if att.get("datas"):
                    attachment = self.env["ir.attachment"].create({
                        "name": att["name"],
                        "type": "binary",
                        "datas": base64.b64decode(att["datas"]),  # decode back to bytes
                        "mimetype": att.get("mimetype", "application/pdf"),
                        "res_model": "account.move",
                        "res_id": invoice.id,
                    })
                    # replace with id, for sending mail
                    new_widget.append({
                        "id": attachment.id,
                        "name": attachment.name,
                        "mimetype": attachment.mimetype,
                        "type": "binary",
                    })

            # Update wizard attachments with real ids
            wizard.mail_attachments_widget = new_widget

        # Call super to actually send the email
        return super().action_send_and_print()
