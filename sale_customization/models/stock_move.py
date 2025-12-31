# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'

    actual_demand_qty = fields.Float(
        string="Actual Demand Qty",
        default=lambda self: self.product_uom_qty,
    )
    actual_demand_remark = fields.Char(string="Remark For Actual Demand")

    # ------------------------------
    # CREATE: Set default value
    # ------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            move.actual_demand_qty = move.product_uom_qty
        return moves

    # --------------------------------------------------------
    # UI Onchange Validation (Delivery Only)
    # --------------------------------------------------------
    @api.onchange('actual_demand_qty', 'product_uom_qty')
    def _onchange_limit_actual_and_qty(self):
        for move in self:
            if move.picking_type_id.code != 'outgoing':
                continue  # Only apply on Delivery Orders

            # ---- actual_demand_qty <= product_uom_qty ----
            if move.actual_demand_qty and move.product_uom_qty:
                if move.actual_demand_qty > move.product_uom_qty:
                    raise ValidationError(_(
                        "Actual Demand (%s) cannot be greater than Ordered Quantity (%s) "
                        "for product %s."
                    ) % (
                        move.actual_demand_qty,
                        move.product_uom_qty,
                        move.product_id.display_name
                    ))

            # # ---- quantity <= actual_demand_qty ----
            if move.quantity:
                move.quantity = move.actual_demand_qty
            #     if move.quantity > move.actual_demand_qty:
            #         raise ValidationError(_(
            #             "Quantity (%s) cannot be greater than Actual Demand (%s) "
            #             "for product %s."
            #         ) % (
            #             move.quantity,
            #             move.actual_demand_qty,
            #             move.product_id.display_name
            #         ))
