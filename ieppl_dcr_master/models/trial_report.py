from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.orm.fields_relational import Many2one


class TrialReport(models.Model):
    _name = "trial.report"
    _description = "Trial Report"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one("res.partner", string="Client", required=True, domain="[('is_company', '=', True)]")
    user_ids = fields.Many2many('res.users', string="Salesperson")
    name = fields.Char(string="Cell No", default=lambda self: "New")
    display_name = fields.Char(string="Display Name")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    brand_id = fields.Many2one('brand.master', string="Brand", required=True)
    dcr_id = fields.Many2one("dcr.master", string="DCR")
    dcr_domain = fields.Char(default="[]")
    lead_id = fields.Many2one("crm.lead", string="Lead")
    lead_domain = fields.Char(default="[]")
    application_id = fields.Many2one("product.application", string="Application")
    app_domain = fields.Char(default="[]")
    show_fuchs = fields.Boolean(compute="_compute_show_brand")
    show_loctite = fields.Boolean(compute="_compute_show_brand")
    show_sandvik = fields.Boolean(compute="_compute_show_brand")
    # For Fuchs brand
    machine_model_id = fields.Many2one("machine.model", string="Machine Name / Number")
    coolant_brand_id = fields.Many2one('brand.master', string='Coolant Brand')
    coolant_id = fields.Many2one("product.product", string="Coolant Name")
    coolant_brand_domain = fields.Char()
    r_i_factor = fields.Float(string="R I Factor(%)")
    tank_cap = fields.Char(string="Tank Capacity")
    tank_cleaned_date = fields.Date(string="Tank Cleaned / Date of Charge", default=fields.Datetime.now, )
    recom_const = fields.Float(string="Recommended Concentration(%)")

    # For Loctite brand
    testing_supervision = fields.Char(string='Testing under supervision of')
    testing_datetime = fields.Datetime(string='Date & time of testing')
    strength = fields.Char(string='Strength(N/m²)')
    pressure = fields.Char(string='Pressure')
    temperature = fields.Char(string='Temperature(°C)')

    test_procedure = fields.Html(sanitize=True)
    result = fields.Text(string='Result')
    remarks = fields.Text(string='Remarks, if any')

    #for sandvik
    date = fields.Date(
        string="Date",
        default=lambda self: fields.Date.today()
    )

    # product_type=fields.
    line_ids = fields.One2many('trial.report.line', 'report_id', string="Report Lines")

    @api.depends('brand_id')
    def _compute_show_brand(self):
        for rec in self:
            brand_name = (rec.brand_id.name or '').lower()

            rec.show_fuchs = 'fuchs' in brand_name
            rec.show_loctite = 'loctite' in brand_name
            rec.show_sandvik = 'sandvik' in brand_name

    @api.onchange('partner_id', 'brand_id', 'lead_id', 'dcr_id')
    def _onchange_domains(self):
        for rec in self:
            # ----------------------------------------------------
            # LEAD DOMAIN
            # ----------------------------------------------------
            lead_domain = [('user_id', '=', rec.env.user.id), ('dcr_id', '!=', False)]
            if rec.partner_id:
                lead_domain = ['|', ('partner_id', '=', rec.partner_id.id),
                               ('partner_id.commercial_partner_id', '=', rec.partner_id.id), ] + lead_domain
            if rec.brand_id:
                lead_domain.insert(0, ('brand_id', '=', rec.brand_id.id))
            if rec.dcr_id:
                lead_domain.insert(0, ('dcr_id', '=', rec.dcr_id.id))
            rec.lead_domain = str(lead_domain)
            # ----------------------------------------------------
            # DCR DOMAIN
            # ----------------------------------------------------
            dcr_domain = [('application_ids', '!=', False), ('user_id', '=', rec.env.user.id)]
            if rec.lead_id:
                dcr_domain.insert(0, ('lead_ids', 'in', rec.lead_id.id))
            else:
                if rec.partner_id:
                    dcr_domain = ['|', ('partner_id', '=', rec.partner_id.id),
                                  ('partner_id.commercial_partner_id', '=', rec.partner_id.id), ] + dcr_domain
                if rec.brand_id:
                    dcr_domain.insert(0, ('user_brand_id', '=', rec.brand_id.id))
            rec.dcr_domain = str(dcr_domain)

            # ----------------------------------------------------
            # APPLICATION DOMAIN
            # ----------------------------------------------------
            if rec.dcr_id:
                app_domain = [('dcr_form_id', '=', rec.dcr_id.id)]
            else:
                app_domain = []
                if rec.partner_id:
                    app_domain = ['|', ('dcr_form_id.partner_id', '=', rec.partner_id.id),
                                  ('dcr_form_id.partner_id.commercial_partner_id', '=', rec.partner_id.id)] + app_domain
                if rec.brand_id:
                    app_domain.append(('product_brand_id', '=', rec.brand_id.id))

            rec.app_domain = str(app_domain)

            # ----------------------------------------------------
            # AUTO-SET LOGIC
            # ----------------------------------------------------
            # Auto-set DCR from lead
            if rec.lead_id and rec.lead_id.dcr_id:
                rec.dcr_id = rec.lead_id.dcr_id

            # Auto-set lead from DCR (first lead)
            if rec.dcr_id and rec.dcr_id.lead_ids:
                if not rec.lead_id:
                    rec.lead_id = rec.dcr_id.lead_ids[0]

            # Auto-set application
            if rec.dcr_id:
                apps = rec.dcr_id.application_ids
            else:
                apps = self.env['product.application']

            if rec.brand_id:
                apps = apps.filtered(lambda a: a.product_brand_id == rec.brand_id)

            rec.application_id = apps[:1].id if apps else False

            # ----------------------------------------------------
            # CLEAR INVALID VALUES
            # ----------------------------------------------------
            if rec.lead_id:
                # if rec.partner_id and (
                #         rec.lead_id.partner_id != rec.partner_id or rec.lead_id.partner_id.commercial_partner_id != rec.partner_id):
                #     rec.lead_id = False
                if rec.brand_id and rec.lead_id.brand_id != rec.brand_id:
                    rec.lead_id = False
                if rec.dcr_id and rec.lead_id.dcr_id != rec.dcr_id:
                    rec.lead_id = False

            if rec.dcr_id:
                if rec.partner_id and rec.dcr_id.partner_id != rec.partner_id:
                    rec.dcr_id = False
                if rec.brand_id and rec.dcr_id.user_brand_id != rec.brand_id:
                    rec.dcr_id = False

    @api.onchange('application_id')
    def _onchange_application_id(self):
        """Triggered when the application_id changes to update related values."""
        if self.application_id:
            if not self.dcr_id:
                self.dcr_id = self.application_id.dcr_form_id
            if self.application_id.machine_model_id:
                self.machine_model_id = self.application_id.machine_model_id
            if self.application_id.coolant_id:
                self.coolant_id = self.application_id.coolant_id


            # ------------------------------
            # Auto-create FIRST LINE based on application
            # ------------------------------
            app = self.application_id

            if not self.line_ids:
                self.line_ids = [(0, 0, {
                    'tool_manufacturer_id': app.tool_manufacturer_id.id,
                    'tool_code': app.tool_code,
                    'insert_manufacturer_id': app.insert_manufacturer_id.id,
                    'insert_code': app.insert_code,
                    'geometry_grade': app.geometry_grade,
                    'inserts_in_tool': app.inserts_in_tool,
                    'tool_cost': app.tool_cost,
                    'edges_per_insert': app.edges_per_insert,
                    'cost_per_insert': app.cost_per_insert,
                    'cutting_cutter_diameter': app.cutting_cutter_diameter,
                    'cutting_speed_vc': app.cutting_speed_vc,
                    'spindle_speed_rpm': app.spindle_speed_rpm,
                    'feed_per_tooth_fz': app.feed_per_tooth_fz,
                    'feed_vf': app.feed_vf,
                    'cutting_depth_ap': app.cutting_depth_ap,
                    'working_engage_ae': app.working_engage_ae,
                    'length_of_cut': app.length_of_cut,
                    'number_of_passes': app.number_of_passes,
                    'time_in_cut_operation': app.time_in_cut_operation,
                    'total_cycle_time': app.total_cycle_time,
                    'tool_life': app.tool_life,
                    'criteria_for_tool_change': app.criteria_for_tool_change.id,
                })]

    def action_trial_sandvik(self):
        for rec in self:
            if rec.brand_id and rec.brand_id.name == 'Sandvik':
                if rec.application_id:
                    app = rec.application_id
                    rec.write({
                        'line_ids': [(0, 0, {
                            'tool_manufacturer_id': app.tool_manufacturer_id.id,
                            'tool_code': app.tool_code,
                            'insert_manufacturer_id': app.insert_manufacturer_id.id,
                            'insert_code': app.insert_code,
                            'geometry_grade': app.geometry_grade,
                            'inserts_in_tool': app.inserts_in_tool,
                            'tool_cost': app.tool_cost,
                            'edges_per_insert': app.edges_per_insert,
                            'cost_per_insert': app.cost_per_insert,
                            'cutting_cutter_diameter': app.cutting_cutter_diameter,
                            'cutting_speed_vc': app.cutting_speed_vc,
                            'spindle_speed_rpm': app.spindle_speed_rpm,
                            'feed_per_tooth_fz': app.feed_per_tooth_fz,
                            'feed_vf': app.feed_vf,
                            'cutting_depth_ap': app.cutting_depth_ap,
                            'working_engage_ae': app.working_engage_ae,
                            'length_of_cut': app.length_of_cut,
                            'number_of_passes': app.number_of_passes,
                            'time_in_cut_operation': app.time_in_cut_operation,
                            'total_cycle_time': app.total_cycle_time,
                            'tool_life': app.tool_life,
                            'criteria_for_tool_change': app.criteria_for_tool_change.id,
                        })]
                    })
            else:
                raise ValidationError(_("This button works only for Sandvik brand."))

    @api.onchange('coolant_brand_id')
    def _onchange_coolant_brand_id(self):
        for rec in self:
            if rec.coolant_brand_id:
                # Filter by selected make
                rec.coolant_brand_domain = str([('brand_id', '=', rec.coolant_brand_id.id)])
            else:
                # Show ALL models
                rec.coolant_brand_domain = "[]"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            seq = self.env['ir.sequence'].next_by_code('trial.report.sequence') or '0000'
            vals['name'] = seq
            # build display name
            if vals.get('brand_id'):
                brand = self.env['brand.master'].browse(vals['brand_id'])
                vals['display_name'] = f"{brand.name}-{seq}"
            else:
                vals['display_name'] = seq
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'brand_id' in vals and rec.name:  # rec.name = sequence
                brand = rec.brand_id
                seq = rec.name
                rec.display_name = f"{brand.name}-{seq}" if brand else seq
        return res

    @api.onchange('dcr_id')
    def _onchange_dcr_id(self):
        if self.dcr_id:
            self.user_ids = self.dcr_id.user_ids
        else:
            admin_user = self.env.ref('base.user_admin')
            self.user_ids = [(6, 0, [admin_user.id])]

    def action_preview_application(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Application Preview',
            'res_model': 'product.application',
            'view_mode': 'form',
            'res_id': self.application_id.id,
            'target': 'current',
        }

class TrialReportLine(models.Model):
    _name = "trial.report.line"
    _description = "Trial Report Line"

    water_ph = fields.Float(string="Water pH")
    report_id = fields.Many2one(
        'trial.report',
        string="Trial Report")
    date = fields.Date(
        string="Date",
        default=lambda self: fields.Date.today(),
        required=True
    )
    concentration = fields.Char(string="CONCENTRATION (REFRACTOMETER) BEFORE")
    ph = fields.Float(string="pH")
    oil_top_up = fields.Float(string="Oil Top Up (Ltrs)")
    water_top_up = fields.Float(string="Water Top Up (Ltrs)")

    # for sandvik
    tool_manufacturer_id = fields.Many2one("res.partner", string="Tool Manufacturer",
                                           domain="[('metal_cutting_mfg', '=', True)]")
    tool_code = fields.Char(string="Tool Code")
    inserts_in_tool = fields.Integer(string="No. of Inserts in Tool")
    tool_cost = fields.Float(string="Tool Cost")
    entering_angle = fields.Float(string="Entering Angle (°)")
    insert_indexing_time = fields.Float(string="Insert Indexing Time")
    insert_manufacturer_id = fields.Many2one("res.partner", string="Insert Manufacturer",
                                             domain="[('metal_cutting_mfg', '=', True)]")
    insert_code = fields.Char(string="Insert Code")
    geometry_grade = fields.Char(string="Geometry & Grade")
    edges_per_insert = fields.Integer(string="Edges Per Insert")
    cost_per_insert = fields.Float(string="Cost of Insert")
    cutting_cutter_diameter = fields.Float(string="Cutting / Cutter Diameter (ϕ)", help="Diameter of cutter in mm")
    cutting_speed_vc = fields.Float(string="Cutting Speed (Vc)", help="Cutting speed in m/min")
    spindle_speed_rpm = fields.Float(string="Spindle Speed (RPM)")
    feed_per_tooth_fz = fields.Float(string="Feed per Tooth (Fz)", help="Feed per tooth in mm")
    feed_vf = fields.Float(string="Feed (Vf)", help="Feed in mm/min")
    cutting_depth_ap = fields.Float(string="Cutting Depth (ap)", help="Depth of cut in mm")
    working_engage_ae = fields.Float(string="Working Engage (ae)", help="Width of cut in mm")
    length_of_cut = fields.Float(string="Length of Cut")
    number_of_passes = fields.Integer(string="No. of Passes")
    time_in_cut_operation = fields.Float(string="Time in Cut of Operation", help="Actual cutting time in minutes")
    total_cycle_time = fields.Float(string="Total Cycle time of Job", help="Overall job cycle time in minutes")
    tool_life = fields.Integer(string="Tool Life", help="Number of jobs per tool")
    criteria_for_tool_change = fields.Many2one("tool.criteria", string="Criteria for Tool Change")
    remarks=fields.Char(string="Remarks")
    user_id=fields.Many2one('res.users',string='Salesperson')
    contact_person=Many2one('res.users',string='Contact person')

    @api.onchange('water_ph', 'ph')
    def _onchange_water_ph_limit(self):
        for record in self:
            if record.water_ph > 12.0 or record.ph > 12.0:
                raise ValidationError(_("Water pH Or pH cannot be greater than 12."))
            elif record.water_ph < 0.0 or record.ph < 0.0:
                raise ValidationError(_("Water pH Or pH cannot be lesser than 0.0"))
