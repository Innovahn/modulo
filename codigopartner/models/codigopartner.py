# -*- encoding: utf-8 -*-
from openerp import models, fields

class Codigopartner(osv.Model):
    _inherit = 'res.partner'
    _columns = {
            'partnercode' : fields.char("Autorización",size=32),
            }
