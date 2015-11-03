# -*- encoding: utf-8 -*-
from openerp import models, fields
class Facturascontrato(models.Model):
    _inherit="account.invoice"
    contrato_ids=fields.Many2one("contratos.contractsale","No. de Contrato",ondelete="set null",domain=[('active', '=', True)],
                               help="Contratos asociados a clientes",index=True)
    _defaults={
           'partner_id' : lambda self, cr, uid, context : context['partner_id'] if context and 'partner_id' in context else None,               
            }