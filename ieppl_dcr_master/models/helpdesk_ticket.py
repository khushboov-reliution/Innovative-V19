from odoo import api, fields, models, tools
from odoo.exceptions import AccessError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    dcr_id = fields.Many2one('dcr.master', string='DCR Reference', help='Reference to the DCR Master record')
    contact_person = fields.Many2one('res.partner', string='Contact Person',domain="[('parent_id','=',partner_id)]")

    brand_id = fields.Many2one('brand.master', string='Brand')
    # application_type_id = fields.Many2one('application.type', string='Application Type',domain="[('brand_id','child_of',brand_id)]")
    product_id = fields.Many2one('product.product', string='Product')

