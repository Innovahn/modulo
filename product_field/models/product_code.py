# -*- encoding: utf-8 -*-
from openerp import models, fields

class Productcode(models.Model):
    _inherit = 'product.product'
    product_code = fields.Char("Color Secundario",size=32)
