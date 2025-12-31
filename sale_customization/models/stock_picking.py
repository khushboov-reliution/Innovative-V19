# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_id = fields.Many2one('account.move', string='Invoice')

    def button_validate(self):
        for picking in self:
            # Apply only for Delivery Orders
            if picking.picking_type_id.code != 'outgoing':
                continue

            for move in picking.move_ids:
                # # Check: move.quantity <= actual_demand_qty
                # if move.actual_demand_qty and move.quantity:
                #     if move.quantity > move.actual_demand_qty:
                #         raise ValidationError(_(
                #             "Delivered Quantity (%s) cannot be greater than Actual Demand (%s) for product %s."
                #         ) % (move.quantity, move.actual_demand_qty, move.product_id.display_name))
                # Check: actual_demand_qty <= product_uom_qty
                if move.actual_demand_qty and move.product_uom_qty:
                    if move.actual_demand_qty > move.product_uom_qty:
                        raise ValidationError(_(
                            "Actual Demand (%s) cannot be greater than Ordered Quantity (%s) for product %s."
                        ) % (move.actual_demand_qty, move.product_uom_qty, move.product_id.display_name))

        # Auto Create Invoice on delivery order validation
        res = super().button_validate()
        for picking in self.filtered(lambda p: p.state == 'done' and p.picking_type_code == "outgoing"):
            sale_order = picking.sale_id
            if sale_order:
                invoices = sale_order._create_invoices(final=True)
                if invoices:
                    picking.invoice_id = invoices[0].id
        return res

    def invoice_button(self):
        for picking in self:
            if picking.invoice_id:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Invoice',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': picking.invoice_id.id,
                    'target': 'current',
                }
