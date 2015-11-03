# -*- encoding: utf-8 -*-


from openerp import fields, models
from openerp.addons import decimal_precision as dp


class ProductProduct(models.Model):

    _inherit = 'product.product'

    cost_price = fields.Float(
        string="Variant Cost Price", digits=dp.get_precision('Product Price'),
        groups="base.group_user", company_dependent=True)
