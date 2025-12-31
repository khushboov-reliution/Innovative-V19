# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    header = fields.Binary(string='Company Header')
    footer = fields.Binary(string='Company Footer')
    bank_id = fields.Many2one('res.partner.bank', string=' Sale Bank')