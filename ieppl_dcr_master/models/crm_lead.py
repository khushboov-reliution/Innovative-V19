from odoo import api, fields, models
from odoo.tools import html2plaintext

class CrmLead(models.Model):
    _inherit = "crm.lead"

    description_plain = fields.Text(
        string="Notes",
        compute="_compute_plain_description",store=True,
    )

    @api.depends('description')
    def _compute_plain_description(self):
        for p in self:
            p.description_plain = html2plaintext(p.description or "")

    # if use below inverse method than change html(tag) into plain text but in export file tag is display.
    # thats why only added new field and in that convert this into text for exporting tag is not display.
    # while exporting leads the added new field is export so it print plain text.

    # def _inverse_plain_description(self):
    #     for p in self:
    #         if p.description_plain:
    #             content = p.description_plain
    #             p.description = content
    #         else:
    #             p.description = False

    dcr_id = fields.Many2one("dcr.master", string="Source DCR", domain="[('lead_ids', '=', False)]")
    application_ids = fields.One2many("product.application", "lead_id", string="Applications")
    referred_id = fields.Many2one("res.users", string="Referred Person", default=lambda self: self.env.user,
                                  readonly=True)
    brand_id = fields.Many2one("brand.master", string="Brand", related="dcr_id.user_brand_id")
    cross_ref_brand_id = fields.Many2one("brand.master", string="Cross Ref Brand")
    app_product_ids = fields.Many2many("product.product", string="Product")
    lead_line_ids = fields.One2many(
        comodel_name="crm.lead.line", inverse_name="lead_id", string="Lead Lines"
    )


    @api.onchange("lead_line_ids")
    def _onchange_lead_line_ids(self):
        expected_revenue = 0
        for lead_line in self.lead_line_ids:
            expected_revenue += lead_line.expected_revenue
        self.expected_revenue = expected_revenue

    def _convert_opportunity_data(self, customer, team_id=False):
        res = super()._convert_opportunity_data(customer, team_id)
        expected_revenue = 0
        for lead_line in self.lead_line_ids:
            expected_revenue += lead_line.expected_revenue
        res["expected_revenue"] = expected_revenue
        return res

    def action_sale_quotations_new(self):
        sale_order_lines = []
        for line in self.lead_line_ids:
            sale_order_lines.append((0, 0, {
                'brand_id': line.product_brand_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'price_unit': line.price_unit or 0.0,
            }))
        action = super(CrmLead, self).action_sale_quotations_new()
        action["context"] = dict(action.get("context", {}), default_dcr_id=self.dcr_id.id,
                                 default_brand_id=self.brand_id.id,
                                 default_order_line=sale_order_lines,
                                 default_opportunity_id=self.id)
        return action
