# -*- encoding: utf-8 -*-
from openerp import models
from openerp.tools.translate import _
class purchase_order(models.Model):
        _inherit = 'purchase.order'
	
	def view_invoice(self, cr, uid, ids, context=None):
		for po in self.browse(cr, uid, ids, context=context):
			curr_id = po.currency_id.id
		ctx=super(purchase_order,self).view_invoice(cr, uid, ids, context=context)
		ctx = dict(ctx or {})
		ctx.update({'context' : {'type':'in_invoice', 'journal_type': 'purchase','purch_curr_id' : curr_id}})
		return ctx

	
