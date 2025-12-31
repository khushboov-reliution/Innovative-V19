# -*- coding: utf-8 -*-
from odoo import fields, models

class PackingForwarding(models.Model):
    _name = 'packing.details'
    _rec_name = 'packing'

    packing = fields.Char(string='Packing & Forwarding')


class InsuranceDetails(models.Model):
    _name = 'insurance.details'
    _rec_name = 'insurance'

    insurance = fields.Char(string='Description')

class DispatchDetails(models.Model):
    _name = 'dispatch.details'
    _rec_name = 'dispatch_through'

    dispatch_through = fields.Char(string='Dispatch Through')

class PickingPolicy(models.Model):
    _name = 'picking.policy'
    _rec_name = 'picking_policy'

    picking_policy = fields.Char(string='Picking Policy')