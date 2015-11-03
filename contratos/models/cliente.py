# -*- encoding: utf-8 -*-
from openerp import models, fields
class Contratocliente(models.Model):
        _inherit = 'res.partner'
        contratos_ids= fields.One2many("contratos.contractsale","partner_id", string="Contratos")