from email.policy import default

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class MachineMaster(models.Model):
    _name = "machine.master"
    _description = "Machine Make / Machine"

    name = fields.Char("Machine Make", required=True)
    machine_model_ids = fields.One2many(
        "machine.model",
        "machine_make_id",
        string="Machine Models"
    )

    active = fields.Boolean(default=True)


class MachineModel(models.Model):
    _name = "machine.model"
    _description = "Machine Model"
    _rec_name = "machine_model"

    machine_type = fields.Char(string="Machine Type")
    machine_series = fields.Char(string="Machine Series")
    machine_model = fields.Char(string="Machine Model")
    machine_make_id = fields.Many2one("machine.master", string="Machine Make")
    active = fields.Boolean(default=True)


class OperationMaster(models.Model):
    _name = "operation.master"
    _description = "Operation Master"

    name = fields.Char("Operation", required=True)

    active = fields.Boolean(default=True)


class RPSurfaceMaster(models.Model):
    _name = "surface.master"
    _description = "RP Surface Master"

    name = fields.Char(required=True)


# -----------------------------
# For Sandvik
# -----------------------------

class CoolantMaster(models.Model):
    _name = "coolant.master"
    _description = "Coolant Master"
    _rec_name = "coolant_make"

    coolant_make = fields.Char("Coolant Make", required=True)
    grade = fields.Char("Coolant Grade")
    price = fields.Float("Coolant Price")
    consumption = fields.Float("Coolant Consumption (Ltr)")

    active = fields.Boolean(default=True)


class ToolCriteria(models.Model):
    _name = "tool.criteria"
    _description = "Tool Criteria"

    name = fields.Char(required=True)


class LoctiteChemicalDetails(models.Model):
    _name = "loctite.chemical.details"
    _description = "Loctite Chemical Details"

    application_id = fields.Many2one("product.application")
    chemical_type = fields.Char(string="Chemical Type")
    temp_c = fields.Float(string="Tempo °C")
    concentrate_ppm = fields.Float(string="Concentrate ppm")
    ph_range = fields.Float(string="Ph range", help="Ph range continuous /intermittent")
    dissolved_solids = fields.Char(string="Dissolved solids", help="Dissolved solids if any, pls describe")

    @api.onchange('ph_range')
    def _check_ph_range(self):
        for rec in self:
            # Allow empty / zero if needed, adjust as per business logic
            if rec.ph_range is not False:
                if rec.ph_range < 0.0 or rec.ph_range > 14.0:
                    raise ValidationError("pH range must be between 0 and 14.")


class LoctiteEquipmentHistory(models.Model):
    _name = "loctite.equipment.history"
    _description = "Loctite Equipment History"

    application_id = fields.Many2one("product.application")
    equipment_name = fields.Char(string="Equipment type/name")
    original_coating = fields.Char(string="Original coated or unprotected")
    maintenance_interval = fields.Char(string="Av. Maint. Intervals")
    repair_cost = fields.Char(string="Cost of repair &/or replacement")
    substrate_type = fields.Char(string="Substrate type")
    structurally_sound = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="")
    base_frame_info = fields.Char(string="")


# -----------------------------
# For Loctite
# -----------------------------
class EndProductCategory(models.Model):
    _name = "end.product.category"
    _description = "End Product Category"

    name = fields.Char(string="Category Name", required=True)
    description = fields.Text(string="Description")


class EndProduct(models.Model):
    _name = "end.product"
    _description = "End Product"

    name = fields.Char(string="End Product Name", required=True)
    category_ids = fields.Many2many(
        "end.product.category",
        "end_product_category_rel",
        "end_product_id",
        "category_id",
        string="Categories"
    )
    active = fields.Boolean(default=True)


class AssemblyMaster(models.Model):
    _name = "assembly.master"
    _description = "Assembly Master"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)


class AssemblyComponent(models.Model):
    _name = "assembly.component"
    _description = "Assembly Component"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)


class SolutionProductMaster(models.Model):
    _name = "solution.product.master"
    _description = "Solution Product Master"

    application_id = fields.Many2one('product.application', string="Product Application", ondelete='cascade')
    dcr_form_id = fields.Many2one('dcr.master',related="application_id.dcr_form_id")
    product_id = fields.Many2one("product.product", string="Proposed Product",
                                 domain="[('brand_id','child_of',product_brand_id)]")
    solution_product_quantity = fields.Float(string="Quantity", default=1.0)
    solution_product_uom = fields.Many2one('uom.uom', string="UoM", related='product_id.uom_id')
    solution_product_price = fields.Monetary(string="Price", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    frequency = fields.Selection([('weekly', 'Weekly'),
                                  ('daily', 'Daily'),
                                  ('monthly', 'Monthly'),
                                  ('quarterly', 'Quarterly'),
                                  ('yearly', 'Yearly'),
                                  ('one-time', 'One-time')], string='Frequency', default='monthly')
    solution_proposed = fields.Text(string="Remarks", help="Auto-filled from Product + SKU but can be edited manually.")
    product_brand_id = fields.Many2one('brand.master', default=lambda self: self.application_id.product_brand_id,
                                       string="Brand", store=True, readonly=False)
    brand_domain = fields.Char()

    @api.depends('product_id')
    def _compute_solution_product_details(self):
        for rec in self:
            if rec.product_id:
                product = rec.product_id
                # Get price based on customer's pricelist (from DCR)
                rec.solution_product_price = rec._get_price_from_customer_pricelist(product)

    # -------------------------------------------------------------------------
    # fetch price from customer pricelist
    # -------------------------------------------------------------------------
    def _get_price_from_customer_pricelist(self, product):
        """Return product price based on DCR customer's pricelist.
           If product not found in pricelist, add it automatically.
        """
        self.ensure_one()
        partner = self.application_id.dcr_form_id.partner_id if self.application_id.dcr_form_id else False
        qty = 1.0

        # Default fallback
        price = product.list_price

        if not partner or not partner.property_product_pricelist:
            return price

        pricelist = partner.property_product_pricelist

        # Search if this product already exists in pricelist items
        item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_id', '=', product.id)
        ], limit=1)

        if not item:
            # Add a new product item in the pricelist
            self.env['product.pricelist.item'].create({
                'pricelist_id': pricelist.id,
                'applied_on': '1_product',
                'product_id': product.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'compute_price': 'fixed',
                'fixed_price': self.solution_product_price,
            })

        # Now return the computed price
        price = pricelist._get_product_price(product, qty)
        return price
