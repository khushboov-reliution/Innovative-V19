# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    discount_slab_id = fields.Many2one('discount.slab')
    brand_id = fields.Many2one("brand.master", string="Brand", domain="[('is_competitor','=', False)]")
    contact_person = fields.Many2one('res.partner', string='Contact Person')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            rec.brand_id = rec.partner_id.brand_id

    def print_quotation(self):
        return self.env.ref('ieppl_purchase_customization.action_report_purchase_order_modified').report_action(self)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    brand_id = fields.Many2one("brand.master", string="Brand")
    brand_domain = fields.Char()

    @api.onchange('order_id')
    def _onchange_order_set_brand(self):
        if self.order_id and self.order_id.brand_id:
            self.brand_id = self.order_id.brand_id.id
        else:
            self.brand_id = False

    @api.onchange('brand_id')
    def _onchange_brand_domain(self):
        for line in self:
            if line.brand_id:
                return {
                    'domain': {
                        'product_id': [('brand_id', '=', line.brand_id.id), ]
                    }
                }
            else:
                return {
                    'domain': {
                        'product_id': [('brand_id.is_competitor', '=', False)]
                    }
                }

    @api.onchange('brand_id')
    def _onchange_brand_po(self):
        for line in self:
            domain = []
            if line.brand_id:
                domain.append(('brand_id', '=', line.brand_id.id))
            line.brand_domain = domain

    # @api.onchange('product_id','order_id.partner_id')
    # def _onchange_last_purchase_price(self):
    #     for rec in self:
    #         vendor = rec.order_id.partner_id
    #         product = rec.product_id
    #
    #         if not vendor or not product:
    #             continue
    #
    #         last_po_line = self.env['purchase.order.line'].search([
    #             ('product_id', '=', product.id),
    #             ('order_id.partner_id', '=', vendor.id),
    #             ('order_id.state', '=', 'purchase'),
    #         ], order='date_order DESC', limit=1)
    #
    #         if last_po_line:
    #             # rec.last_purchase_price = last_po_line.price_unit
    #             rec.price_unit = last_po_line.price_unit

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(PurchaseOrderLine, self).create(vals_list)
        lines._apply_purchase_discount()
        return lines

    def write(self, vals):
        res = super(PurchaseOrderLine, self).write(vals)
        # Recalculate discount only if vendor or product changed
        if any(f in vals for f in ['product_id', 'order_id']):
            self._apply_purchase_discount()
        return res

    def _apply_purchase_discount(self):
        """Auto-apply discount based on vendor’s total sales slab."""
        DiscountSlab = self.env['discount.slab']

        for line in self:
            order = line.order_id

            # Ensure sale orders are flushed to DB so query sees latest totals
            # SaleOrder.flush(['amount_total', 'state', 'partner_id'])

            # ✅ Get total confirmed & done sales for this vendor
            self.env.cr.execute("""
                SELECT COALESCE(SUM(amount_total), 0)
                FROM sale_order
                WHERE state IN ('sale', 'done')
            """)
            row = self.env.cr.fetchone()
            total_sales = (row and row[0]) or 0.0
            # ✅ Find the applicable discount slab
            slab = DiscountSlab.search([
                ('min_sales_target', '<=', total_sales)
            ], order='min_sales_target desc', limit=1)

            if slab:
                line.discount = slab.discount_percentage
                # optional: show slab on PO
                order.discount_slab_id = slab.id
