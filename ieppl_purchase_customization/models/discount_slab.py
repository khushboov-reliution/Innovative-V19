from odoo import models, fields, api


class DiscountSlab(models.Model):
    _name = 'discount.slab'
    _description = 'Discount Slab'

    name = fields.Char(required=True)
    min_sales_target = fields.Monetary(
        required=True,
        currency_field='currency_id',
        help="Minimum cumulative sales to qualify"
    )
    discount_percentage = fields.Float(required=True, help="Discount % to apply on next PO")
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
