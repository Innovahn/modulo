# -*- coding: utf-8 -*-

import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import api
from datetime import datetime
class sales_forecast_calculate(osv.osv_memory):

	_name = 'sales.forecast.calculate.wizard'
	
	def get_days_percent(self, cr, uid,ids,date_from, date_to,oper, context=None):
		diferencia = None
		diferencia = datetime.strptime(date_to,'%Y-%m-%d') - datetime.strptime(date_from,'%Y-%m-%d')
		res = 0.0
		if date_from not in [None,False] and date_to not in [None,False] and oper not in [None,False]:
			if oper == 'daily':
				res = float(diferencia.days)
			elif oper == 'weekly':
				res = float(diferencia.days)/7
			elif oper == 'monthly':
				res = float(diferencia.days)/30
			else:
				res = float(diferencia.days)/360
			return res
		else:
			return False
	def get_line(self, cr, uid,ids,forecast_id, lista_order_lines, producto_id,date_from, date_to,oper,growht_rate, context=None):
		resultado = []
		sale_order_pool = self.pool.get('sale.order.line')
		order_lines = []
		sale_order_lines_obj = sale_order_pool.browse(cr, uid,sale_order_pool.search(cr, uid,[('id' , 'in' ,lista_order_lines),('product_id' , '=' , producto_id)],context = context),context = context )
		productos_evaluados = []
		cantidad_total = 0.0
		total_amount = 0.0
		increment_cant = 0.0
		increment_amount = 0.0
		porcent = 0.0	
		for order_line in sale_order_lines_obj:
			cantidad_total += order_line.product_uos_qty
			total_amount += order_line.price_unit
		line = {}
		line = dict(line or {})
		porcent = self.get_days_percent(cr, uid,ids,date_from, date_to,oper, context = context)
		if int(growht_rate) > 0:
			increment_amount = float(total_amount/porcent)*(float(growht_rate)/100)
			increment_cant = float(cantidad_total/porcent)*(float(growht_rate)/100)
			cantidad_total = float(cantidad_total/porcent) + increment_cant
			total_amount = float(total_amount/porcent) + increment_amount
		else:
			cantidad_total = float(cantidad_total/porcent) 
			total_amount = float(total_amount/porcent)
		line.update({'sale_forecast_id': forecast_id,'auto_quantity': cantidad_total,'auto_amount': total_amount})
		line.update({'product_id': producto_id,'manual_quantity': cantidad_total,'manual_amount': total_amount})		
		return line


	def get_forecast_line(self, cr, uid,ids,currency_id,forecast_id, date_from, date_to,oper,growht_rate, context=None):
		resultado = []
		sale_order_pool = self.pool.get('sale.order')
		sale_forecast_objects = sale_order_pool.browse(cr, uid,sale_order_pool.search(cr, uid,[('pricelist_id.currency_id.id','=',currency_id),('state','=','done'),('date_order', '>', date_from),('date_order', '<=', date_to)],context = context),context = context )
		lista_productos = []
		lista_order_lines = []		
		for objects in sale_forecast_objects:
			for order_line in objects.order_line:
				if order_line.product_id.id not in lista_productos:
					lista_productos.append(order_line.product_id.id)
				lista_order_lines.append(order_line.id)
		productos_evaluados = []	
		for producto in lista_productos:
			line = False
			line = self.get_line(cr, uid, ids, forecast_id ,lista_order_lines, producto,date_from, date_to, oper,growht_rate,context = context)
			resultado.append(line)
		
		return resultado
	def calculate_sales_forecast(self, cr, uid,ids, context=None):
		context = dict(context  or {})
		if context.get('sale_forecast_id',False):
			sale_forecast_pool = self.pool.get('sale.forecast')
			sale_forecast_pool.write(cr, uid,context.get('sale_forecast_id'),{'sale_forecast_line' : False, 'was_calculated' : True,'msj_hide':None,'msj' : None}, context=context)
			sale_forecast_pool_line = self.pool.get('sale.forecast.line')
			sale_forecast_pool_line.unlink(cr, uid,sale_forecast_pool_line.search(cr,uid,[('sale_forecast_id','=',context.get('sale_forecast_id'))],context=context),context=context)
			res = self.get_forecast_line(cr, uid, ids,context.get('currency_id',False),context.get('sale_forecast_id',False) , context.get('date_from',False),context.get('date_to',False), context.get('process',False),context.get('growht_rate',False),context = context)
			for l in res:
				sale_forecast_obj = sale_forecast_pool_line.create(cr, uid, l, context = context)
		

	_columns = {
		'name': fields.char('Name'),
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
		
	}

	_defaults = {
		'date_from': lambda self, cr, uid, context: context['date_from'] if context and  context['date_from'] not in [False,None] else  False,
		'date_to': lambda self, cr, uid, context: context['date_to'] if context and  context['date_to'] not in [False,None] else  False,
		'process': lambda self, cr, uid, context: context['process'] if context and  context['process'] not in [False,None] else  False,
		'growht_rate': lambda self, cr, uid, context: context['growht_rate'] if context and  context['growht_rate'] not in [False,None] else  False,
		'currency_id' : lambda self, cr, uid, context: context['currency_id'] if context and  context['currency_id'] not in [False,None] else  False,
	} 






