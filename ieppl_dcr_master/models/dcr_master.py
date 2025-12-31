from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup

import logging
import datetime

_logger = logging.getLogger(__name__)


class DCRMaster(models.Model):
    _name = "dcr.master"
    _description = "DCR Master"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_user_brand(self):
        user = self.env.user
        brand = self.env['brand.master'].search([('user_ids', 'in', user.id), ('is_competitor', '=', False)], limit=1)
        return brand.id

    name = fields.Char(copy=False, readonly=True, required=True,
                       default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    active = fields.Boolean(string="Active", default=True)
    # visit_type_id = fields.Many2one("mail.activity.type", string="Visit Type",required=True)
    mode_of_engagement = fields.Selection([
        ('visit', 'Visit'),
        ('call', 'Call'),
    ], string='Mode of Engagement', default='visit')
    visit_type = fields.Selection([
        ('single', 'Single'),
        ('joint', 'Joint'),
    ], string='Visit Type', default='single')
    call_type = fields.Selection([
        ('single', 'Single'),
        ('conference', 'Conference'),
    ], string='Call Type', default='single')
    user_ids = fields.Many2many('res.users', string="Salespersons")

    # Section 1 – Customer & Visit Info
    user_id = fields.Many2one("res.users", string="Salesperson", default=lambda self: self.env.user, readonly=True)
    user_brand_id = fields.Many2one(
        'brand.master',
        string="Brand", tracking=True,
        domain="[('user_ids', 'in', user_id),('is_competitor','=',False)]", default=_default_user_brand,
    )
    is_fuchs_brand = fields.Boolean()
    is_sandvik_brand = fields.Boolean()
    is_loctite_brand = fields.Boolean()
    dcr_type = fields.Selection([('follow_up', 'Follow-Up Visit'),
                                 ('lead', 'Lead'),
                                 ('payments', 'Payment Collection'),
                                 ('helpdesk_ticket', 'Issue Visit'),
                                 ('trial_project', 'Trial Project')],
                                string="DCR Type", default="follow_up", required=True)
    partner_id = fields.Many2one("res.partner", string="Customer", domain="[('is_company', '=', True)]", required=True)
    contact_person = fields.Many2one('res.partner', string='Contact Person', context={"from_dcr": True},
                                     domain="[('parent_id','=',partner_id)]")
    industry = fields.Many2one("res.partner.industry", string="Industry", related='partner_id.industry_id',
                               readonly=False, tracking=True)
    location = fields.Char(string="Location")
    date_visit = fields.Datetime(string="Date of Visit", default=fields.Datetime.now, readonly=True)

    # Product-specific
    fuchs_product_type = fields.Selection([
        ('neat_oil', 'Neat Oil'),
        ('water_soluble', 'Water Soluble'),
        ('rust_preventive', 'Rust Preventive'),
    ], string='Product Type', default="neat_oil")

    loctite_product_type = fields.Selection([('oem', 'OEM'), ('mro', 'MRO')], default="oem", string="Product Type")

    # Section 2 – Current Visit Purpose
    application_ids = fields.One2many('product.application', 'dcr_form_id', string="Application")

    # Section 3 – Cross-Reference
    cross_ref = fields.Boolean(string="Cross-Reference ?")
    cross_ref_ids = fields.One2many('dcr.cross.ref', 'dcr_form_id', string="Cross References")

    # Section 4 – Competitor Insights
    competitor_ids = fields.One2many("competition.master", "dcr_form_id", string='Competitor Product')

    lead_ids = fields.One2many(
        "crm.lead",
        "dcr_id", context={"active_test": False},
        string="Generated Leads"
    )
    lead_count = fields.Integer(
        string="Leads Count",
        compute="_compute_lead_count"
    )

    lead_existing_id = fields.Many2one(
        "crm.lead",
        string="Existing Lead",
        domain="[('dcr_id', '=', False)]"
    )
    helpdesk_ids = fields.One2many(
        "helpdesk.ticket",
        "dcr_id",
        string="Generated Tickets"
    )
    helpdesk_count = fields.Integer(
        string="Helpdesk Count",
        compute="_compute_helpdesk_count"
    )

    expense_count = fields.Integer(
        compute="_compute_expense_count",
        string="Expense Count"
    )

    add_expense = fields.Boolean(string="Add Expense")

    expense_ids = fields.One2many('hr.expense', 'dcr_id', string="Expenses")
    note = fields.Text()

    @api.onchange('user_brand_id')
    def _onchange_user_brand_id(self):
        for rec in self:
            brand_name = (rec.user_brand_id.name or '').lower()

            rec.is_fuchs_brand = 'fuchs' in brand_name
            rec.is_loctite_brand = 'loctite' in brand_name
            rec.is_sandvik_brand= 'sandvik' in brand_name

            if not rec.is_fuchs_brand:
                rec.fuchs_product_type = False
            else:
                if not rec.fuchs_product_type:
                    rec.fuchs_product_type = 'neat_oil'

            if not rec.is_loctite_brand:
                rec.loctite_product_type = False
            else:
                if not rec.loctite_product_type:
                    rec.loctite_product_type = 'oem'

    # -------------------------
    # FOLLOW-UP SECTION
    # -------------------------
    followup_purpose = fields.Char(string="Visit Purpose", tracking=True)
    followup_summary = fields.Text(string="Discussion Summary / Remarks", tracking=True)
    next_visit_date = fields.Datetime(string="Next Visit Date", tracking=True)
    next_visit_commitment = fields.Char(string="Commitment / Action Points", tracking=True)

    # domain passed to the field in the view
    lead_domain = fields.Char(string="Lead Domain", default="[]")

    @api.onchange('partner_id', 'contact_person', 'dcr_type')
    def _onchange_partner_contact(self):
        for rec in self:
            # only apply when dcr_type == 'lead'
            if rec.dcr_type != 'lead':
                rec.lead_domain = "[]"
                continue
            base = [('dcr_id', '=', False)]
            if rec.contact_person:
                domain = base + [('partner_id', '=', rec.contact_person.id)]
            elif rec.partner_id:
                domain = base + [('partner_id.commercial_partner_id', '=', rec.partner_id.id)]
            else:
                domain = [('id', '=', 0)]
            rec.lead_domain = str(domain)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.name or record.name == _('New'):
                record.name = self.env['ir.sequence'].next_by_code('dcr.master') or _('New')
        return records

    @api.onchange('next_visit_date')
    def _onchange_next_visit_date(self):
        for rec in self:
            if rec.next_visit_date and rec.date_visit:
                if rec.next_visit_date < rec.date_visit:
                    raise ValidationError("Next Visit Date cannot be before Date of Visit.")

    def get_salesperson_activities_records(self, **kwargs):
        activity = self.env['log.activity'].search(
            [('res_id', '=', kwargs['id']), ('model_id', '=', kwargs['resModel'])])

        if not activity:
            self.user_id.salesperson_activities.create({
                'salesperson_id': self.user_id.id,
                'name': self.name,
                'model_id': kwargs['resModel'],
                'res_id': self.id,
                'log_time': datetime.datetime.now(),
                'latitude': kwargs['lat'],
                'longitude': kwargs['long'],
            })

    # Helper that creates missing leads for application lines (idempotent)
    def _ensure_application_leads(self):
        Lead = self.env["crm.lead"]
        LeadLine = self.env["crm.lead.line"]

        for rec in self:
            # --- Cross Ref Leads ---
            if rec.cross_ref:
                for ref in rec.cross_ref_ids:
                    brand = ref.brand_id
                    salesperson = ref.salesperson_id
                    note = ref.note or "Cross-reference Lead"
                    # crm_teams = self.env['crm.team'].search([('brand_id', '=', brand.id)])

                    Lead.create({
                        'name': f"{rec.name}[ CROSS-REF ] Brand – {brand.name}",
                        'partner_id': rec.partner_id.id,
                        'contact_name': rec.contact_person.name if rec.contact_person else False,
                        'type': 'lead',
                        'description': note,
                        # 'team_id': team.id,
                        'brand_id': brand.id,
                        'user_id': salesperson.id if salesperson else False,
                        'dcr_id': rec.id,
                        'cross_ref_brand_id': brand.id,
                        'referred_id': rec.user_id.id,
                    })

            if rec.lead_existing_id:
                continue

            # --- Application Leads ---
            for app in rec.application_ids:
                if not app.solution_product_ids:
                    continue
                lead = Lead.create({
                    'name': f"{rec.name}[ APPLICATION ]",
                    'partner_id': rec.partner_id.id,
                    'contact_name': rec.contact_person.name if rec.contact_person else False,
                    'type': 'lead',
                    'description': app.other_details,
                    'brand_id': app.product_brand_id.id,
                    'user_id': rec.user_id.id,
                    'dcr_id': rec.id,
                })
                for sol in app.solution_product_ids:
                    LeadLine.create({
                        'lead_id': lead.id,
                        'product_id': sol.product_id.id,
                        'product_qty': sol.solution_product_quantity or 1.0,
                        'uom_id': sol.solution_product_uom.id if sol.solution_product_uom else False,
                        'price_unit': sol.solution_product_price or 0.0,
                        'name': sol.solution_proposed or '',
                        'product_brand_id': sol.product_brand_id.id if sol.product_brand_id else False,
                    })

                app.lead_id = lead.id

    @api.onchange('lead_existing_id')
    def _onchange_lead_existing_id(self):
        if not self.lead_existing_id:
            return

        lead = self.lead_existing_id

        if lead.user_id:
            self.user_ids = [(6, 0, [lead.user_id.id])]
        else:
            admin_user = self.env.ref('base.user_admin')
            self.user_ids = [(6, 0, [admin_user.id])]

        partner = lead.partner_id
        # 1. Auto-set partner + contact
        if partner:
            # If this is a contact and has a parent company
            if partner.parent_id:
                # Set company
                self.partner_id = partner.parent_id.id
                # Contact is the partner itself
                self.contact_person = partner.id
            else:
                # This is a company
                self.partner_id = partner.id

                # Now find its contact based on lead.contact_name
                if lead.contact_name:
                    contact = self.env['res.partner'].search([
                        ('name', '=', lead.contact_name),
                        ('parent_id', '=', partner.id),
                    ], limit=1)
                    if contact:
                        self.contact_person = contact.id

        if lead.contact_name and self.partner_id:
            contact = self.env['res.partner'].search([
                ('name', '=', lead.contact_name),
                ('parent_id', '=', self.partner_id.id)
            ], limit=1)
            if contact:
                self.contact_person = contact.id

        # 2. Auto-set brand
        if lead.brand_id:
            self.user_brand_id = lead.brand_id.id

        # 3. Auto-set referred user
        if lead.referred_id:
            self.user_id = lead.referred_id.id

        # # 4. Merge lead lines into applications
        # application = self.application_ids[:1]
        #
        # # If no application exists → create one in onchange using fake record
        # if not application:
        #     application = self.env['product.application'].new({
        #         'dcr_form_id': self.id,
        #     })
        #     self.application_ids += application
        #
        # # Existing product IDs
        # existing_products = application.solution_product_ids.mapped('product_id').ids
        #
        # # Add new lines
        # new_solution_lines = []
        # for line in lead.lead_line_ids:
        #     if line.product_id.id not in existing_products:
        #         new_solution_lines.append((0, 0, {
        #             'product_id': line.product_id.id,
        #             'solution_product_quantity': line.product_qty,
        #             'solution_product_price': line.price_unit,
        #             'solution_proposed': line.name,
        #             'solution_product_uom': line.uom_id.id if line.uom_id else False,
        #         }))
        #
        # if new_solution_lines:
        #     application.solution_product_ids = new_solution_lines

    @api.onchange('dcr_type', 'contact_person', 'lead_existing_id')
    def _onchange_salesperson_flow(self):
        if self.dcr_type != 'lead':
            return

        if self.lead_existing_id:
            lead = self.lead_existing_id

            if lead.user_id:
                self.user_ids = [(6, 0, [lead.user_id.id])]
            else:
                admin = self.env.ref('base.user_admin', raise_if_not_found=False)
                if admin:
                    self.user_ids = [(6, 0, [admin.id])]
            return

        if self.contact_person and not self.lead_existing_id:
            admin = self.env.ref('base.user_admin', raise_if_not_found=False)
            if admin:
                self.user_ids = [(6, 0, [admin.id])]

    def _compute_lead_count(self):
        for rec in self:
            rec.lead_count = len(rec.lead_ids)

    @api.depends('helpdesk_ids')
    def _compute_helpdesk_count(self):
        for rec in self:
            rec.helpdesk_count = len(rec.helpdesk_ids)

    @api.depends('expense_ids')
    def _compute_expense_count(self):
        for rec in self:
            rec.expense_count = len(rec.expense_ids)

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                continue

            # -----------------------------
            # VALIDATION FOR LEAD TYPE DCR
            # -----------------------------
            if rec.dcr_type == "lead":
                LeadLine = self.env["crm.lead.line"]

                # Must have either Application or Cross-Ref
                if not rec.application_ids and not rec.cross_ref:
                    raise ValidationError(
                        _("Cannot confirm DCR without any Application or Cross-Reference data.")
                    )

                # If using existing lead
                if rec.lead_existing_id:
                    lead = rec.lead_existing_id

                    # Set DCR on lead
                    if not lead.dcr_id:
                        lead.dcr_id = rec.id

                    # -----------------------------
                    # UPDATE LEAD LINE IDS
                    # -----------------------------
                    for app in rec.application_ids:

                        for sol in app.solution_product_ids:

                            # Check if product already exists in lead lines
                            existing_line = lead.lead_line_ids.filtered(
                                lambda l: l.product_id.id == sol.product_id.id
                            )

                            if not existing_line:
                                LeadLine.create({
                                    'lead_id': lead.id,
                                    'product_id': sol.product_id.id,
                                    'product_qty': sol.solution_product_quantity or 1.0,
                                    'uom_id': sol.solution_product_uom.id if sol.solution_product_uom else False,
                                    'price_unit': sol.solution_product_price or 0.0,
                                    'name': sol.solution_proposed or sol.product_id.name,
                                    'product_brand_id': sol.product_brand_id.id if sol.product_brand_id else False,
                                })

                        # Always map app to this lead
                        app.lead_id = lead.id

            # -----------------------------
            # CROSS REF VALIDATION
            # -----------------------------
            if rec.cross_ref and not rec.cross_ref_ids:
                raise ValidationError(
                    _("Cross-Reference is checked, but no Cross-Reference entries found.")
                )
            rec._ensure_application_leads()
            # ------------------------------------
            # FOLLOW-UP TYPE DCR LOGIC
            # ------------------------------------
            if rec.dcr_type == "follow_up":

                if rec.next_visit_date:
                    rec._onchange_next_visit_date()

                if not rec.followup_purpose:
                    raise ValidationError(_("Visit Purpose is required for Follow-Up DCR."))

                # Log a note in customer chatter
                message = Markup("""
                <b>Follow-Up Visit (%(dcr_name)s)</b><br/><br/>
                <b>Purpose:</b> %(purpose)s<br/>
                <b>Summary:</b> %(summary)s<br/>
                <b>Next Visit:</b> %(next_visit)s<br/>
                <b>Commitment:</b> %(commitment)s<br/>
                """) % {
                    'dcr_name': rec.name,
                    'purpose': rec.followup_purpose or '',
                    'summary': rec.followup_summary or '',
                    'next_visit': rec.next_visit_date or '',
                    'commitment': rec.next_visit_commitment or '',
                }

                rec.partner_id.message_post(body=message)

                # Create DONE activity for THIS visit (today)
                self.env["mail.activity"].create([
                    {
                        "res_model_id": self.env["ir.model"]._get_id("res.partner"),
                        "res_id": rec.partner_id.id,
                        "activity_type_id": self.env.ref("mail.mail_activity_data_meeting").id,
                        "summary": f"Follow-Up Visit Completed - {rec.followup_purpose}",
                        "note": rec.followup_summary or "Visit completed.",
                        "user_id": rec.user_id.id,
                        "date_deadline": fields.Date.today(),
                        "state": "done",
                    }
                ])

                # -----------------------------
                # Create Next Visit Activity
                # -----------------------------
                if rec.next_visit_date:
                    self.env["mail.activity"].create([
                        {
                            "res_model_id": self.env["ir.model"]._get_id("res.partner"),
                            "res_id": rec.partner_id.id,
                            "date_deadline": rec.next_visit_date.date(),
                            "activity_type_id": self.env.ref("mail.mail_activity_data_meeting").id,
                            "summary": rec.next_visit_commitment or "Next Follow-Up Visit",
                            "note": rec.followup_summary or "",
                            "user_id": rec.user_id.id,
                        }
                    ])
                # Popup
                if self.user_id and self.user_id.partner_id:
                    self.env['bus.bus']._sendone(
                        self.user_id.partner_id,
                        'simple_notification',
                        {
                            'title': "Confirmation",
                            'message': f"Visit confirmed for {self.partner_id.name}",
                            'sticky': False,
                        })
            rec.state = 'confirmed'
        return True

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
        return True

    def action_cancel(self):
        for rec in self:
            # Cancel the DCR itself
            rec.state = 'cancelled'

            # Cancel related leads
            if rec.lead_ids:
                rec.lead_ids.action_set_lost()

            # Close related helpdesk tickets like a normal stage change
            if rec.helpdesk_ids:
                close_stage = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Cancelled')], limit=1)
                if close_stage:
                    now = fields.Datetime.now()
                    rec.helpdesk_ids.write({
                        'stage_id': close_stage.id,
                        'last_stage_update': now,
                        'closed_date': now,
                    })

        return True

    def action_view_leads(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Leads"),
            "res_model": "crm.lead",
            "view_mode": "list,form",
            "domain": [("dcr_id", "=", self.id), "|", ("active", "=", True), ("active", "=", False)],
            "context": {"default_dcr_id": self.id},
        }

    def action_create_helpdesk_ticket(self):
        return {
            'name': 'New Helpdesk Ticket',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'view_id': self.env.ref('ieppl_dcr_master.helpdesk_ticket_view_form').id,
            'target': 'new',  # This makes it a popup
            'context': {
                'default_dcr_id': self.id,
                'default_name': f'Ticket From DCR {self.name}',
                'default_partner_id': self.partner_id.id,
                'default_contact_person': self.contact_person.id,
                'default_brand_id': self.user_brand_id.id,
            },
        }

    def action_view_helpdesk(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Quotations"),
            "res_model": "helpdesk.ticket",
            "view_mode": "list,form",
            "domain": [("dcr_id", "=", self.id)],
            "context": {'default_dcr_id': self.id},
        }

    def action_open_expenses(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("DCR Expenses"),
            "res_model": "hr.expense",
            "view_mode": "list,form",
            "domain": [("dcr_id", "=", self.id)],
            "context": {"default_dcr_id": self.id},
        }

        # Computed field to control button visibility

    show_trial_button = fields.Boolean(
        string="Show Trial Report Button",
        compute='_compute_show_trial_button'
    )

    @api.depends('state', 'user_brand_id')
    def _compute_show_trial_button(self):
        for rec in self:
            brand_name = (rec.user_brand_id.name or '').lower()
            rec.show_trial_button = (
                    rec.state == 'confirmed' and
                    (
                            'fuchs' in brand_name or
                            'sandvik' in brand_name or
                            'loctite' in brand_name
                    )
            )

    # Action to open Trial Report using context
    def action_open_trial_report(self):
        self.ensure_one()

        if self.state != 'confirmed':
            raise ValidationError("You can create the Trial Report only after confirming the DCR.")

        return {
            'name': "Trial Report",
            'type': 'ir.actions.act_window',
            'res_model': 'trial.report',
            'view_mode': 'form',
            'view_id': self.env.ref('ieppl_dcr_master.view_trial_report_form').id,
            'target': 'current',
            'context': {
                'default_dcr_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_brand_id': self.user_brand_id.id,
                'default_user_ids': [(6, 0, self.user_ids.filtered(lambda u: u.active).ids)],
            }
        }

class ProductApplication(models.Model):
    _inherit = "product.application"

    dcr_form_id = fields.Many2one('dcr.master')
    lead_id = fields.Many2one('crm.lead', string="Linked Lead")


class CompetitionMaster(models.Model):
    _inherit = "competition.master"

    dcr_form_id = fields.Many2one('dcr.master')
    application_id = fields.Many2one("product.application")


class HrExpense(models.Model):
    _inherit = "hr.expense"

    dcr_id = fields.Many2one('dcr.master', string="Linked DCR", ondelete="cascade")

    @api.onchange('product_id')
    def _onchange_product_id_refresh_name(self):
        """Refresh name every time category (product) is changed."""
        for exp in self:
            product = exp.product_id
            if product:
                exp.name = exp.product_id.display_name
