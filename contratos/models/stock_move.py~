# -*- encoding: utf-8 -*-
from openerp import models, fields, api
class Stockcontrato(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'
    contrato_stock_ids=fields.Many2one("contratos.contractsale","Contract No.",ondelete="set null", help="Contratos asociados a clientes",index=True)
    quantity_total=fields.Float(
        string='# de Productos', compute='_get_qty_total', store=True)

    @api.one
    @api.depends("move_lines", "move_lines.product_qty")
    def _get_qty_total(self):
                self.quantity_total= sum([x.product_qty for x in self.move_lines])

     
    
