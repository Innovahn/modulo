# -*- coding: utf-8 -*-
from openerp import models, api
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from datetime import datetime
import locale
import pytz
from openerp.tools.translate import _
import time
from time import gmtime, strftime
from itertools import ifilter
class sales_forecast(osv.Model):
	_name = "sale.forecast"
	
	
		
	def calculate_forecast(self, cr, uid,ids, context=None):
		dummy, view_id_form  = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sales_forecast_innova', 'view_sale_forecast_calculate_form')
		if not ids: return []
		context.update({'sale_forecast_id': ids[0]})
		for x in self.browse(cr, uid, ids, context = context):
			context.update({'date_to': x.date_to,'date_from': x.date_from,'process': x.process,'growht_rate': x.growht_rate,'currency_id': x.currency_id.id,})
		return {
			'name':_("Sale Forecast Calculate"),
			'view_type': 'form',
		   	'res_model': 'sales.forecast.calculate.wizard',
		    	'type': 'ir.actions.act_window',
			'context': context,
			'views': [(view_id_form, 'form')],
			'nodestroy': True,
		    	'target': 'new',
		    	'domain': '[]'
			}
	
	def unlink(self, cr, uid, ids, context=None):
		for obj in self.browse(cr, uid, ids, context = context):
			if obj.state  not in ['draft']:
				raise osv.except_osv(_('Error!'),_("You can not delete a document that that is in an state diferent than draft!"))
		return super(sales_forecast, self).unlink(cr, uid, ids, context=context)
		

	def some_change(self,cr,uid,ids,x,context=None):
		msj = None
		msj =  'The process,currency or Growht rate values has changed, you will have to recalculate the values'
		return { 'value' :{ 'msj' : msj, 'msj_hide' : msj }}


	def _get_msg(self,cr, uid, ids, field, arg, context=None):
		result={}
		for x in self.browse(cr,uid,ids,context=context):
			result[x.id] = x.msj_hide
		return result

	def validate(self,cr, uid, ids, context=None):
		if self.write(cr,uid,ids,{'state':'done'},context=context):
			return True
		return False
	def cancel(self,cr, uid, ids, context=None):
		if self.write(cr,uid,ids,{'state':'cancel'},context=context):
				return True
		return False
	_columns = {
		'name': fields.char('Name'),
		'msj': fields.function(_get_msg, type='char',  store=False),
		'msj_hide': fields.char('Message',stored=False),
		'date_from':fields.date('From',  select=True,required=False ),
		'date_to':fields.date('To',  select=True,required=False ),
		'process':fields.selection([
			('daily','Daily'),
			('weekly','Weekly'),
			('monthly','monthly'),
			('annual','Annual'),
			],'Type', ),
		'growht_rate' : fields.integer('Growth Rate',),
		'currency_id':fields.many2one('res.currency', 'Currency', copy=False),
		'state':fields.selection(
		    [('draft','Draft'),
		     ('done','Validated'),
		     ('cancel','Cancel'),
		    ], 'Status',),
		'was_calculated' : fields.boolean('Was Calculated',),
		'sale_forecast_line' : fields.one2many('sale.forecast.line','sale_forecast_id',),	
		}
	_defaults = {
		'state' : 'draft',
		'date_from': lambda *a: time.strftime('%Y-%m-%d'),
		'date_to': lambda *a: time.strftime('%Y-%m-%d'),
		}


class sale_forecast_line(osv.Model):
	_name = "sale.forecast.line"

	def _get_factor1(self, cr, uid, ids, field, arg, context=None):
		result = {}
		for obj in self.browse(cr,uid,ids,context=context):
			if obj.manual_quantity > 0 and obj.auto_quantity > 0:
				result[obj.id] = (obj.manual_quantity/obj.auto_quantity)*100
		return result	

	def _get_factor2(self, cr, uid, ids, field, arg, context=None):
		result = {}
		result = {}
		totalc=0
		for obj in self.browse(cr,uid,ids,context=context):
			if obj.auto_amount > 0 and obj.manual_amount > 0:
				result[obj.id] = (obj.manual_amount/obj.auto_amount)*100
		return result

	def _get_sum(self, cr, uid, ids, field, arg, context=None):
		result = {}
		result = {}
		totalc=0
		for obj in self.browse(cr,uid,ids,context=context):
			if (obj.factor1 + obj.factor2) < 200:
				result[obj.id] = False
			else:
				result[obj.id] = True
		return result

	def onchange_value(self,cr,uid,ids,valor1,valor2,op,context=None):
		n=0
		n = (float(valor1)/valor2)*100
		if op==1:
			return { 'value' :{ 'factor1' : n }}
		else:
			return { 'value' :{ 'factor2' : n }}
	_columns = {
		'sale_forecast_id' : fields.many2one('sale.forecast','Sale Forecast id',),
		'product_id' : fields.many2one('product.product','Product',),
		'auto_quantity' : fields.float('Auto. Quantity',),
		'auto_amount' : fields.float('Auto. Amount',),
		'manual_quantity' : fields.float('Manual Quantity',),
		'manual_amount' : fields.float('Manual Amount',),
		'factor1' : fields.function(_get_factor1,type='integer',string='Factor1', ), 	 
		'factor2' : fields.function(_get_factor2,type='integer',string='Factor2', ),
		'sum' : fields.function(_get_sum,type='boolean',string='Sum',stored=False ),			
		}

