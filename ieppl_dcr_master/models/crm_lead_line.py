# Copyright (C) 2017-2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class CrmLeadLine(models.Model):
    _name = "crm.lead.line"
    _description = "Line in CRM Lead"

    @api.depends("price_unit", "product_qty")
    def _compute_expected_revenue(self):
        for rec in self:
            rec.expected_revenue = rec.product_qty * rec.price_unit

    @api.depends("lead_id.probability", "expected_revenue")
    def _compute_prorated_revenue(self):
        for rec in self:
            if rec.lead_id and rec.lead_id.type != "lead":
                rec.prorated_revenue = (
                    rec.expected_revenue * rec.lead_id.probability * (1 / 100)
                )

    lead_id = fields.Many2one("crm.lead", string="Lead")
    name = fields.Char("Description", translate=True)
    product_id = fields.Many2one(
        "product.product", string="Product", index=True, domain=[("sale_ok", "=", True)]
    )
    category_id = fields.Many2one(
        "product.category", string="Product Category", index=True
    )
    product_tmpl_id = fields.Many2one(
        "product.template", string="Product Template", index=True
    )
    product_qty = fields.Integer(string="Product Quantity", default=1, required=True)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", readonly=True)
    price_unit = fields.Float(digits="Product Price")
    product_brand_id = fields.Many2one("brand.master", string="Brand")
    # application_type_id = fields.Many2one("application.type", string="Applications")
    company_currency = fields.Many2one(
        "res.currency",
        string="Currency",
        related="lead_id.company_currency",
        readonly=True,
    )
    expected_revenue = fields.Monetary(
        compute="_compute_expected_revenue",
        string="Expected revenue",
        currency_field="company_currency",
        compute_sudo=True,
        store=True,
    )
    prorated_revenue = fields.Monetary(
        compute="_compute_prorated_revenue",
        string="Prorated revenue",
        currency_field="company_currency",
        compute_sudo=True,
        store=True,
    )
    user_brand_ids = fields.Many2many(
        'brand.master',
        default=lambda self: self.env.user.brand_ids,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if not self.lead_id:
            return

        domain = {}

        if self.product_id:
            product = self.product_id

            self.category_id = product.categ_id.id
            self.product_tmpl_id = product.product_tmpl_id.id
            self.price_unit = product.list_price
            self.name = product.name
            self.product_brand_id = product.brand_id.id

            if not self.uom_id or self.uom_id.id != product.uom_id.id:
                self.uom_id = product.uom_id.id
            if self.uom_id.id != product.uom_id.id:
                self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        else:
            self.price_unit = 0.0
            self.name = ""
            self.product_brand_id = False

        return {"domain": {"product_id": domain}}

