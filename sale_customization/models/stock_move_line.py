from odoo import _,api, fields, models

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    pdf_attachment = fields.Binary("Attachment")
    pdf_filename = fields.Char("File Name")


    def _action_done(self):
        res = super()._action_done()

        for line in self:
            if line.lot_id:
                if not line.pdf_attachment:
                    line.pdf_attachment = line.lot_id.attachment_pdf
                    line.pdf_filename = line.lot_id.attachment_filename
                else:
                    line.lot_id.attachment_pdf = line.pdf_attachment
                    line.lot_id.attachment_filename = line.pdf_filename

        return res


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    attachment_pdf = fields.Binary("PDF Attachment", store=True)
    attachment_filename = fields.Char("Filename", store=True)

