# -*- encoding: utf-8 -*-

from openerp import api, tools, SUPERUSER_ID
from openerp.osv import osv, fields, expression
from openerp import models
import openerp.addons.decimal_precision as dp

class ProductProduct(models.Model):
    _inherit = "product.product"

    _columns = {
    	'standard_price': fields.property(type = 'float', digits_compute=dp.get_precision('Product Price'), 
                                          help="Cost price of the product template used for standard stock valuation in accounting and used as a base price on purchase orders. ")
    }
