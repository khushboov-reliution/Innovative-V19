from odoo import models, api,fields

class SaleOrder(models.Model):
    _inherit = "sale.order"

    dcr_id = fields.Many2one("dcr.master", string="DCR Reference", help="Link to the related DCR record.")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self.env.context

        if context.get("default_opportunity_id"):
            opportunity = self.env["crm.lead"].browse(context["default_opportunity_id"])

            # Build sale order lines from CRM product lines
            order_lines = []
            for line in opportunity.lead_line_ids:
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_template_id': line.product_tmpl_id.id,
                    'name': line.name,
                    'product_uom_qty': line.product_qty,
                    'price_unit': line.price_unit,
                }))

            res.update({
                "order_line": order_lines,
            })

        return res