from odoo import models, fields, api

class DCRCrossReference(models.Model):
    _name = "dcr.cross.ref"
    _description = "DCR Cross Reference"
    _rec_name = "brand_id"

    dcr_form_id = fields.Many2one('dcr.master', string="DCR", ondelete="cascade")
    brand_id = fields.Many2one('brand.master', string="Brand", required=True)
    salesperson_id = fields.Many2one('res.users', string="Salesperson", required=True, domain="[('brand_ids', 'in', brand_id)]")
    note = fields.Text(string="Note")
