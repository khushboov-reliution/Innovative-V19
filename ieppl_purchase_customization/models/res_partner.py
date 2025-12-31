# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    brand_id = fields.Many2one("brand.master", string="Brand")
