# -*- coding: utf-8 -*-

import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import api
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
from datetime import datetime,timedelta
class exchange_diff(osv.osv_memory):
	_name = 'retention_lines_assig_wizard'
	
	_columns = {
		'number':fields.char('number',required = False),
		'pay_number' : fields.many2one('account.voucher','Payment ref',required=False),
		'pay_number_check' : fields.many2one('mcheck.mcheck','Payment ref',required=False),
		'date':fields.date('Date',required = False),
		'description': fields.char('Description',copy=False,required=False),
		'retentions_lines' : fields.many2many('retention.lines','id',required=False),
	}
	_order = 'date desc'

	def assingn_line_retention(self, cr, uid, ids, context=None):
		tlaw = self.browse(cr, uid, ids, context=context)
		retention_pool = self.pool.get('retentions')
		retention_lines_pool = self.pool.get('retention.lines')
		context= dict(context or {})
		model = None
		if context.get('active_model'):
			model = context.get('active_model')
		model_pool = self.pool.get(model)
		vals = {}
		vals= dict(vals or {})
		doc_type =  'check'
		if tlaw.pay_number.id not in [False, None]:
			doc_type = 'voucher'
		vals.update({'number' : tlaw.number, 'pay_number' : tlaw.pay_number.id,'pay_number_check' : tlaw.pay_number_check.id, 'doc_type' : doc_type,'date' : tlaw.date,'description' : tlaw.description })
		retention_id = retention_pool.create(cr, uid, vals, context = None)
		for rl in tlaw.retentions_lines:
			retention_lines_pool.write(cr, uid, rl.id, {'retention_id' :retention_id }, context=context)
		if tlaw.pay_number.id not in [False, None]:
			model_pool.write(cr, uid, tlaw.pay_number.id, {'retention_ref' :retention_id }, context=context)
		else:
			model_pool.write(cr, uid, tlaw.pay_number_check.id, {'retention_ref' :retention_id }, context=context)
		dummy, view_id_form  = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'innova_account_plus', 'retentions_view_form')
		return {
			'name':_("Retentions"),
			'view_type': 'form',
		   	'res_model': 'retentions',
		    	'type': 'ir.actions.act_window',
			'context': context,
			'views': [(view_id_form,'form')],
			'res_id' : retention_id,
			'nodestroy': True,
		    	'target': 'current',
		    	'domain': '[]'
			}
	_defaults = {
		'pay_number' : lambda self, cr, uid, context: context['voucher_id'] if context and  context['voucher_id'] not in [False,None] else  False,
		'pay_number_check' : lambda self, cr, uid, context: context['mcheck_id'] if context and  context['mcheck_id'] not in [False,None] else  False,
		'retentions_lines' : lambda self, cr, uid, context: context['retentions_lines'] if context and  context['retentions_lines'] not in [False,None] else  False,
		 } 
