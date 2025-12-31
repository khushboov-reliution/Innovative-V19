from email.policy import default

from odoo import _, api, models, fields
from odoo.exceptions import ValidationError


class ProductApplication(models.Model):
    _name = "product.application"
    _description = "Product Application"
    _rec_name = "complete_name"

    name = fields.Char(copy=False, readonly=True, default=lambda self: _('New'))
    complete_name = fields.Char(string="Display Brand Name", compute="_compute_complete_name", store=True)
    description = fields.Text("Description")
    product_brand_id = fields.Many2one(
        "brand.master",
        string="Primary Brand",
        related="dcr_form_id.user_brand_id"
    )
    user_brand_ids = fields.Many2many(
        'brand.master',
        default=lambda self: self.env.user.brand_ids,
    )
    is_fuchs_brand = fields.Boolean(related="dcr_form_id.is_fuchs_brand")
    material_category_ids = fields.Many2many(
        'product.material.category',
        'product_application_material_categ_rel',
        'application_id',
        'category_id',
        domain="[('id','in', allowed_material_category_ids)]",
        string="Material Categories"
    )

    allowed_material_category_ids = fields.Many2many(
        'product.material.category',
        compute='_compute_material_category_ids',
        string="Allowed Material Categories",
        store=False
    )

    material_ids = fields.Many2many(
        'product.material',
        'product_application_material_rel',
        'application_id',
        'material_id',
        string="Materials"
    )

    # Multiple bond materials
    bond_material_ids = fields.Many2many(
        'product.material',
        'product_application_bond_material_rel',
        'application_id',
        'material_id',
        string="Bond Materials"
    )

    component_name = fields.Char(string="Component Name", help="Name of the component for this material.")

    component_no = fields.Char(string="Component No", readonly=False, help="Number / code of the component.")

    pain_point_category_id = fields.Many2one('product.pain.point.category', string="Pain Point")
    pain_point_id = fields.Many2one('product.pain.point', string="Pain Point")
    current_date = fields.Datetime(default=fields.Datetime.now, string="Created Date")
    # -----------------------------
    # Pain Points & Observations
    # -----------------------------
    corrosion = fields.Boolean("Corrosion")
    corrosion_after_days = fields.Float("After (Days)")

    misting = fields.Boolean("Misting")
    misting_after_days = fields.Float("After (Days)")

    foul_smell = fields.Boolean(string='Foul smell')
    foul_smell_after_days = fields.Float("After (Days)")

    foaming = fields.Boolean(string='Foaming')
    foaming_after_days = fields.Float("After (Days)")

    over_heating = fields.Boolean("Over Heating")
    over_heating_severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Spotting")

    over_heating_pressure = fields.Selection([
        ('bar', 'Bar'),
        ('kg_cm2', 'Kg/cm²')
    ], string="Pressure", default='bar')
    pressure = fields.Float()

    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Spotting")

    skin_irritation = fields.Boolean("Skin Irritation")
    skin_irritation_severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Spotting")
    # ------------------------------
    # Performance Observations
    # ------------------------------
    performance_sump_life = fields.Float(string="Sump Life (months)")
    performance_odour = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Odour")
    performance_color_change = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Color Change")
    performance_run_down = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Run Down")
    performance_spotting = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string="Spotting")
    performance_remark = fields.Text(string="Remark")

    solution_product_ids = fields.One2many('solution.product.master', 'application_id', string="Proposed Products")
    product_category_id = fields.Many2one('product.category', string="Category",
                                          domain="[('brand_id','child_of',product_brand_id)]")
    competition = fields.Boolean(string="Have Competition ?")
    competition_ids = fields.One2many("competition.master", "application_id", string="Competitor Products")

    active = fields.Boolean(default=True)

    # product_domain = fields.Char(default="[]", string="Product Domain")

    fuchs_product_type = fields.Selection(
        related="dcr_form_id.fuchs_product_type",
        string="Product Type",
        store=True,
        readonly=False
    )

    # -----------------------------
    # MACHINE DETAILS
    # -----------------------------
    machine_id = fields.Many2one("machine.master", string="Machine")
    machine_make_id = fields.Many2one("machine.master", string="Machine Make")
    machine_model_id = fields.Many2one(
        "machine.model",
        string="Machine Model", )
    machine_domain = fields.Char()
    operation_id = fields.Many2one("operation.master", string="Operation")
    machine_id_code = fields.Char(string="Machine ID / Code")

    # -----------------------------
    # Sumps and System
    # -----------------------------
    sump_capacity = fields.Float("Sump Capacity")
    stand_type = fields.Selection([
        ('standalone', "Standalone"),
        ('centralised', "Centralised"),
    ], string="Stand Alone / Centralised")

    other_details = fields.Text("Other Details")

    # -----------------------------
    # RUST PREVENTIVE FIELDS
    # -----------------------------

    filtration = fields.Selection([
        ('magnetic', 'Magnetic'),
        ('paper', 'Paper'),
        ('other', 'Other'),
    ], string="Filtration")

    filtration_other = fields.Char("Other Filtration")

    skimmer = fields.Selection([
        ('available', 'Available'),
        ('not_available', 'Not Available'),
    ], string="Skimmer")

    # Water Details
    water_source = fields.Selection([
        ('ro', 'RO'),
        ('dm', 'DM'),
        ('others', 'Others'),
    ], string="Water Source")

    water_source_other = fields.Char("Other Source")

    # Hardness
    hardness_analysed = fields.Boolean("Hardness Analysed?")
    total_hardness = fields.Float("Total Hardness (ppm)")
    chloride = fields.Float("Chloride (ppm)")
    ph_value = fields.Float("pH")

    # ------------------------------
    # Rust-Preventive – Masters
    # ------------------------------
    surface_id = fields.Many2one(
        'surface.master', string="Surface of Parts"
    )
    # -------------------------
    # RUST PREVENTIVE SELECTIONS
    # -------------------------

    # Packaging
    rp_packaging = fields.Selection([
        ('none', 'No Packaging'),
        ('µm_PE_foil', 'µm PE foil'),
        ('single', 'Single Packed'),
        ('closed', 'Closed Packaging'),
        ('open', 'Open Packaging'),
        ('oil_paper', 'Oil Paper'),
        ('µm_vci_foil', 'µm VCI foil'),
        ('vci', 'VCI'),
        ('rack', 'Rack'),
        ('oil_paper_coats', 'Oil Paper Coats'),
    ], string="Packaging")

    # Transport
    rp_transport = fields.Selection([
        ('none', 'No Transport'),
        ('regional', 'Regional'),
        ('national', 'National'),
        ('europe', 'Europe'),
        ('sea_lower_deck', 'Sea Transport Lower Deck'),
        ('sea_upper_deck', 'Sea Transport Upper Deck'),
    ], string="Transport")

    # Storage Conditions
    rp_storage = fields.Selection([
        ('hall', 'Hall'),
        ('hovel', 'Hovel'),
        ('outdoor', 'Outdoor'),
        ('tropical', 'Tropical Climate'),
        ('subtropical', 'Subtropical Climate'),
        ('cold', 'Cold Climate'),
        ('monsoon', 'Monsoon'),
        ('moderate', 'Moderate Climate'),
        ('coastline', 'Near Coastline'),
        ('temperatures', 'Temperatures'),
        ('air_humidity', 'Air Humidity')
    ], string="Storage Conditions")

    # Protection Duration
    rp_protection_time = fields.Selection([
        ('1_week', '1 Week'),
        ('1_month', '1 Month'),
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('1_year', '1 Year'),
        ('1_5_years', '1.5 Years'),
        ('3_years', '3 Years'),
        ('5_plus', '> 5 Years')
    ], string="Protection Duration")

    # Coating
    rp_coating = fields.Selection([
        ('none', 'No Coating'),
        ('oily', 'Oily'),
        ('waxy', 'Waxy'),
        ('vaseline', 'Vaseline'),
        ('lt_2', '< 2 µm'),
        ('2_5', '2 – 5 µm'),
        ('gt_5', '> 5 µm'),
        ('dry', 'Dry'),
    ], string="Coating")

    # Characteristics
    rp_characteristics = fields.Selection([
        ('non_thixotropy', 'Non-Thixotropy'),
        ('thixotropy', 'Thixotropy'),
        ('vci', 'VCI Agent'),
        ('voc_free', 'VOC Free'),
        ('solvent_a2', 'Solvent A II'),
        ('solvent_a3', 'Solvent A III'),
        ('aqueous', 'Aqueous'),
        ('ba_free', 'BA-Free')
    ], string="Characteristics")

    # Application Method
    rp_application_method = fields.Selection([
        ('dipping', 'Dipping'),
        ('spraying', 'Spraying'),
        ('brushing', 'Brushing'),
        ('wiping', 'Wiping'),
        ('hot', 'Hot Application'),
        ('drying_possible', 'Dry Possible')
    ], string="Application Method")

    # ------------------------------
    # Process Before/After Operation
    # ------------------------------
    rp_process_before_ids = fields.Many2many(
        'operation.master',
        'rp_before_rel',  # relation table name
        'application_id',  # column for this model
        'operation_id',  # column for the operation.master
        string="Process Before Operation",
    )

    rp_process_after_ids = fields.Many2many(
        'operation.master',
        'rp_after_rel',  # different relation table
        'application_id',  # column for this model
        'operation_id',  # column for the operation.master
        string="Process After Operation",
    )
    # ------------------------------
    # Photos Before/After
    # ------------------------------
    photos_before_ids = fields.Many2many(
        'ir.attachment',
        'product_application_photos_before_rel',
        'application_id',
        'attachment_id',
        string="Photos Before",
        domain=[('mimetype', 'ilike', 'image')],
        help="Upload photos of the part before the process"
    )

    photos_after_ids = fields.Many2many(
        'ir.attachment',
        'product_application_photos_after_rel',
        'application_id',
        'attachment_id',
        string="Photos After",
        domain=[('mimetype', 'ilike', 'image')],
        help="Upload photos of the part after the process"
    )
    # ------------------------------
    # End User Approval
    # ------------------------------
    end_user_approval = fields.Boolean(string="End User Approved?")
    end_user_name = fields.Char(string="Note")
    # ------------------------------

    # -----------------------------
    # Sandvik Fields
    # -----------------------------
    spindle_power = fields.Float(string="Spindle Power (kW)", help="Machine spindle power in kW")
    maximum_rpm = fields.Float(string="Maximum RPM", help="Maximum revolutions per minute of the machine")
    tool_change_time = fields.Float(string="Tool Change Time (sec)", help="Tool changing time in seconds")
    hardness_value = fields.Float(string="Hardness Value", help="Enter hardness value in BHN or HRC")
    hardness_scale = fields.Selection([('bhn', 'BHN'), ('hrc', 'HRC')], default='bhn',
                                      string="Hardness Scale", help="Select hardness scale type")
    jobs_per_setup = fields.Integer(string="Number of Jobs per Setup")
    jobs_per_year = fields.Float(string="Number of Jobs per Year")
    jobs_per_batch = fields.Float(string="Number of Jobs per Batch")
    machine_stability = fields.Selection([
        ('excellent', 'Excellent'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ], string="Machine Stability")
    clamping_condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ], string="Clamping Condition")
    coolant_type = fields.Selection([
        ('dry', 'Dry'),
        ('water_soluble', 'Water Soluble'),
        ('neat_oil', 'Neat Oil'),
    ], string="Coolant Type")
    coolant_brand_id = fields.Many2one('brand.master', string='Coolant Brand')
    coolant_id = fields.Many2one("product.product", string="Coolant")
    coolant_brand_domain = fields.Char()
    coolant_price = fields.Float(string="Coolant Price")
    coolant_consumption = fields.Float(string="Coolant Consumption (Liters)")
    coolant_grade = fields.Char(string="Coolant Grade")
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
    # ----------------------------------------------------
    # FOR Loctite Brand
    # ----------------------------------------------------
    end_product_id = fields.Many2one('end.product', string='End Product')
    end_product_category_ids = fields.Many2many(
        "end.product.category",
        "application_end_product_categ_rel",
        "application_id",
        "category_id",
        string="End Product Categories"
    )
    assembly_id = fields.Many2one('assembly.master', string='Assembly')
    assembly_component_id = fields.Many2one('assembly.component', string='Equipment / Component')
    sketch_attachment_ids = fields.Many2many("ir.attachment", "product_application_attachment_rel",
                                             "application_id", "attachment_id", string="Sketch / Picture",
                                             help="Upload sketches, images or drawings related to this application."
                                             )
    dimension = fields.Char("Dimensions")
    gap = fields.Char("Gap")

    # Corrosion / Erosion Input Fields
    total_immersion = fields.Char()
    intermittent_immersion = fields.Char()
    dry_condition = fields.Char()
    vapour_fumes_detail = fields.Char(string="Vapour/Fumes Details")
    impact_detail = fields.Char()
    cavitation = fields.Char()
    current_abrasion = fields.Char(string="Abrasion Details")
    current_abrasion_particle_size = fields.Float(string="Abrasion Particle Size")
    current_abrasion_particle_quantity = fields.Integer(string="Abrasion Particle Quantity")
    current_wear = fields.Char(string="Wear Details")
    current_wear_particle_size = fields.Float(string="Wear Particle Size")
    current_wear_particle_quantity = fields.Integer(string="Wear Particle Quantity")

    # Temperature
    operating_temp_min = fields.Float("Operating Temp Min (°C)")
    operating_temp_max = fields.Float("Operating Temp Max (°C)")

    min_temperature = fields.Float("Minimum Temperature")
    max_temperature = fields.Float("Maximum Temperature")

    # Application Exposed
    abrasion = fields.Char()
    abrasion_particle_size = fields.Float()
    wear = fields.Char()
    wear_particle_size = fields.Float()
    wear_particle_quantity = fields.Integer()
    dry_service = fields.Char()
    wet_service = fields.Char()

    # Chemical Contact Details (One2many)
    chemical_line_ids = fields.One2many('loctite.chemical.details', 'application_id', string="Chemical Details")

    # Equipment History (One2many)
    equipment_line_ids = fields.One2many('loctite.equipment.history', 'application_id', string="Equipment History")

    # Customer Expectations
    customer_expectations = fields.Text()

    # Application consideration
    surface_prep = fields.Char()
    available_downtime = fields.Integer()
    downtime_frequency = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days')
    ], default='hours')

    area_accessible = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Area Accessible?")

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})

        if self.complete_name:
            default['complete_name'] = f"{self.complete_name} (Copy)"

        solution_lines = []
        for line in self.solution_product_ids:
            solution_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'solution_product_quantity': line.solution_product_quantity,
                'frequency': line.frequency,
                'solution_product_uom': line.solution_product_uom.id,
                'solution_product_price': line.solution_product_price,
                'solution_proposed': line.solution_proposed,
            }))
        default['solution_product_ids'] = solution_lines

        competition_lines = []
        for comp in self.competition_ids:
            competition_lines.append((0, 0, {
                'own_product_id': comp.own_product_id.id,
                'own_brand_id': comp.own_brand_id.id,
                'competitor_product_id': comp.competitor_product_id.id,
                'product_category_id': comp.product_category_id.id,
                'product_quantity': comp.product_quantity,
                'frequency': comp.frequency,
                'tentative_price': comp.tentative_price,
                'concentration': comp.concentration,
            }))
        default['competition_ids'] = competition_lines
        return super().copy(default)

    def btn_duplicate_application_line(self):
        self.ensure_one()

        new_rec = self.copy()

        view_id = new_rec._get_form_view_by_brand()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Application',
            'res_model': new_rec._name,
            'res_id': new_rec.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
        }


    def _get_form_view_by_brand(self):
        self.ensure_one()

        brand_name = (self.product_brand_id.name or '').lower()
        if 'loctite' in brand_name:
            return self.env.ref(
                'ieppl_dcr_master.view_product_application_loctite_brand_form',
                raise_if_not_found=False
            ).id
        elif 'fuchs' in brand_name:
            return self.env.ref(
                'ieppl_dcr_master.view_product_application_fuchs_brand_form',
                raise_if_not_found=False
            ).id

        elif 'sandvik' in brand_name:
            return self.env.ref(
                'ieppl_dcr_master.view_product_application_sandvik_brand_form',
                raise_if_not_found=False
            ).id

        return self.env.ref(
                'ieppl_dcr_master.view_product_application_form'
        ).id

    @api.onchange('ph_value')
    def _check_ph_value(self):
        for rec in self:
            # Allow empty / zero if needed, adjust as per business logic
            if rec.ph_value is not False:
                if rec.ph_value < 0.0 or rec.ph_value > 14.0:
                    raise ValidationError("pH value must be between 0 and 14.")

    @api.depends('product_brand_id')
    def _compute_material_category_ids(self):
        for rec in self:
            if rec.product_brand_id and rec.product_brand_id.material_category_ids:
                # Use ONLY brand-specific categories
                rec.allowed_material_category_ids = rec.product_brand_id.material_category_ids
            else:
                # No material in brand → allow ALL categories
                rec.allowed_material_category_ids = self.env['product.material.category'].search([])

    @api.onchange('machine_make_id')
    def _onchange_machine_make_id(self):
        for rec in self:
            if rec.machine_make_id:
                # Filter by selected make
                rec.machine_domain = str([
                    ('machine_make_id', '=', rec.machine_make_id.id)
                ])
            else:
                # Show ALL models
                rec.machine_domain = "[]"

    @api.onchange('machine_model_id')
    def _onchange_machine_model_id(self):
        """ Auto fill machine_make_id when model is selected """
        for rec in self:
            if rec.machine_model_id and not rec.machine_make_id:
                if rec.machine_model_id.machine_make_id:
                    rec.machine_make_id = rec.machine_model_id.machine_make_id.id

    @api.onchange('coolant_brand_id')
    def _onchange_coolant_brand_id(self):
        for rec in self:
            if rec.coolant_brand_id:
                # Filter by selected make
                rec.coolant_brand_domain = str([
                    ('brand_id', '=', rec.coolant_brand_id.id)
                ])
            else:
                # Show ALL models
                rec.coolant_brand_domain = "[]"

    @api.onchange('coolant_id')
    def _onchange_coolant_id(self):
        """ Auto fill machine_make_id when model is selected """
        for rec in self:
            if rec.coolant_id and not rec.coolant_brand_id:
                if rec.coolant_id.brand_id:
                    rec.coolant_brand_id = rec.coolant_id.brand_id.id

    # Auto-clear dependent fields
    @api.onchange('corrosion')
    def _onchange_corrosion(self):
        if not self.corrosion:
            self.corrosion_after_days = False

    @api.onchange('misting')
    def _onchange_misting(self):
        if not self.misting:
            self.misting_after_days = False

    @api.onchange('foul_smell')
    def _onchange_foul_smell(self):
        if not self.foul_smell:
            self.foul_smell_after_days = False

    @api.onchange('foaming')
    def _onchange_foaming(self):
        if not self.foaming:
            self.foaming_after_days = False

    @api.onchange('over_heating')
    def _onchange_over_heating(self):
        if not self.over_heating:
            self.over_heating_severity = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.name or record.name == _('New'):
                record.name = self.env['ir.sequence'].next_by_code('product.application') or _('New')
        return records

    @api.depends("product_brand_id")
    def _compute_complete_name(self):
        for rec in self:
            brand = rec.product_brand_id.name or "No Brand"
            name = rec.name
            rec.complete_name = f"{name}-{brand}"
