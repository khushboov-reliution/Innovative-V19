# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    metal_cutting_mfg = fields.Boolean(string="Metal Cutting Manufacturer")