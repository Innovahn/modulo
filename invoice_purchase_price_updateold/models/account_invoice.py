# -*- encoding: utf-8 -*-
from openerp import models, api
from openerp.osv import fields, osv
from datetime import datetime
class account_invoice(models.Model):
	last_value = None
    	_inherit = 'account.invoice'

	_columns = {
		'currency_id_orig' : fields.integer('Currency_origen'),
		'price_updated' : fields.boolean('Price Udated', store = True),
		'last_curr_used' : fields.integer('Last Currency used', store = True),
	}
	_defaults = {
		'price_updated' : True	
		    } 
	def onchange_currency_id(self, cr, uid, ids,curr_id,last_curr_used,lineas,dateh, context=None):
		update_array = []
		context = dict(context or context)
		porder_pool = None
		show = False
		valor = {}
		ainv_pool = self.pool.get('account.invoice')
		ainv_obj = ainv_pool.browse(cr, uid, ids, context = context)
		cache = True
		if not dateh:
			dateh = datetime.now()
		for i in self.browse(cr, uid, ids, context = context):
			if i:
				cache = False
		if not cache:
			if context.get('purch_curr_id',False):
				for inv in ainv_obj:
					if inv.currency_id_orig in [None, False]:
						self.write(cr, uid, ids,{'currency_id_orig': context.get('purch_curr_id')},context = context)
					for inv in ainv_obj:
						if inv.last_curr_used in [None, False]:
							self.write(cr, uid, ids,{'last_curr_used': context.get('purch_curr_id')},context = context)
			for inv in ainv_obj:
				if inv.last_curr_used in [None, False]:
					self.write(cr, uid, ids,{'last_curr_used': curr_id},context = context)
			
			for inv in ainv_obj:#commentar
				if inv.currency_id_orig == curr_id:
					show = True
			for i in self.browse(cr, uid, ids, context = context):
				self.update_prices(cr, uid, ids,show,curr_id,i.last_curr_used, context = context)
				self.write(cr, uid, ids,{'last_curr_used': curr_id},context = context)
			return {'value' : {'price_updated': show, 'last_curr_used' : curr_id}}
		else:
			i=0
			lcr = None
			arr = []
			for l in lineas:
				i+=1
				if i !=1 : 
					print l[2]
					arr.append(l[2])
			resultado = None
			if last_curr_used in [None, False]:
				resultado = self.update_prices_cache(cr, uid, ids,show, curr_id, curr_id,arr,dateh , context = context)
			else:
				resultado = self.update_prices_cache(cr, uid, ids,show,curr_id,last_curr_used,arr,dateh , context = context)	
			lcr = curr_id
			return {'value' : {'invoice_line': resultado,'last_curr_used' : lcr}}
			
	
	def create(self, cr, uid, values, context=None):
		values = dict(values or {})
		if values.get('currency_id',False):
			values.update({'last_curr_used': values.get('currency_id',False) })
		b = super(account_invoice, self).create(cr, uid, values, context=context)
		return b
	
	def update_prices(self, cr, uid, ids, updated,actual_curr,invoi_curr, context=None):
		invoice_line_pool  = self.pool.get('account.invoice.line')
		for inv in self.browse(cr, uid, ids):
		    dateh = inv.date_invoice
		    curr_pool  = self.pool.get('res.currency')
		    curr_factor = 0
		    curr_obj = curr_pool.browse(cr, uid, invoi_curr, context = context)
		    inv_curr_obj = curr_pool.browse(cr, uid,actual_curr , context = context)
		    currency = inv_curr_obj.with_context(date=dateh)
		    company_currency = curr_obj.with_context(date=dateh)
		    for line in inv.invoice_line:
			curr_factor = currency.rate/company_currency.rate
	        	new_price = line.price_unit*curr_factor
			invoice_line_pool.write(cr, uid, [line.id], {'price_unit':new_price})
		return True	

	def update_prices_cache(self, cr, uid, ids, updated,actual_curr,invoi_curr, lineas,dateh , context=None):
	    curr_pool = self.pool.get('res.currency')
	    curr_obj = curr_pool.browse(cr, uid, invoi_curr, context = context)
	    inv_curr_obj = curr_pool.browse(cr, uid,actual_curr , context = context)
	    currency = inv_curr_obj.with_context(date=dateh)
	    company_currency = curr_obj.with_context(date=dateh)
	    updated_values = []
	    for line in lineas:
		vl = {}
		curr_factor = currency.rate/company_currency.rate
        	new_price = line['price_unit'] * curr_factor
		updated_values.append({'product_id' :line['product_id'],'quantity' :line['quantity'], 'company_id' : line['company_id'], 'account_id' : line['account_id'], 'price_unit' : new_price})
		
		
	    return updated_values
			


	

