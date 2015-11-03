from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from datetime import datetime
import locale
import pytz
from openerp.tools.translate import _
import time
from itertools import ifilter
class account_exchange_validate(osv.Model):

    
    	_name = 'account.exchange.difference'
	_inherit = ['mail.thread']
	_track = {
        'state': {
            'innova_account_plus.mcheck_state_change': lambda self, cr, uid, obj, context=None: True,
       		 },
	 'move_lines': {
            'innova_account_plus.mcheck_total_change': lambda self, cr, uid, obj, context=None: True,
       		 },
   	 }
	def existen_validated(self, cr, uid, ids, date,currency_id, context=None):
		cr.execute("SELECT COUNT(id) FROM account_exchange_difference AS aed WHERE '"+ date +"' > aed.date AND aed.currency_id = "+ str(currency_id)+" AND aed.state = 'validated'")
		c = cr.fetchone() 
		if c  != None and c != False:
			if c[0] != 0:
				return True
		return False

	def buscar_post_lines(self, cr, uid, ids, account_id, context=None):
		cr.execute("SELECT count(id) FROM account_move_line aml WHERE aml.state = 'draft' AND aml.account_id ="+ str(account_id) )
		c = cr.fetchone() 
		if c  != None and c != False:
			if len(c) > 0:
				return True
		return False

	def create_new(self, cr, uid, ids, context=None):
		context = dict(context or {})
		actual_obj = self.browse(cr, uid , ids, context = context)
		dummy, view_id_form  = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_plus', 'account_plus_exchange_wizard_form')
		context.update({'reccal' : False})
		context.update({'id_exchdif':False})
		context.update({'date_to':False})
		context.update({'date_from':False})
		context.update({'journal_id':False})
		context.update({'currency_id':False})
		
		return {
			'name':_("Exchange Diference Recalcullation"),
			'view_type': 'form',
			'view_mode': 'form',
		   	'res_model': 'exchange_diff_wizard',
		    	'type': 'ir.actions.act_window',
			'context': context,
			'views': [(view_id_form,'form')],
			'nodestroy': True,
		    	'target': 'new',
		    	'domain': '[]'
		}


	def unreconciliate(self, cr, uid, ids, context=None):
		obj_actual = self.browse(cr, uid, ids, context = context)
		if not self.existen_validated( cr, uid, ids, obj_actual.date,obj_actual.currency_id.id , context=context):
			reconcile_pool = self.pool.get('account.move.reconcile')
			move_pool = self.pool.get('account.move')
			move_line_pool = self.pool.get('account.move.line')
			doc_type = ''
			journal_id = False
		
			for actual in self.browse(cr, uid, ids, context=context):
				# refresh to make sure you don't unlink an already removed move
				#journal_id = actual.journal_id.id
				actual.refresh()
				if actual.move_id:
					move_pool.button_cancel(cr, uid, [actual.move_id.id])
					move_pool.unlink(cr, uid, [actual.move_id.id])
			res = {
			    'state':'draft',
			    'move_id':False,
			    'was_unreconcilied' : True,
			}
			self.write(cr, uid, ids, res)
			return True
		else:
			raise osv.except_osv(_('Error!'),_("There are validated documents with a date above "+obj_actual.date+" , you have to unreconciliate!"))
	
		
		
	def get_balance(self, cr, uid, ids,account_pool,date_from,date_to,  context=None):
		if context is None:
			context = {}
		c = context.copy()
		if len(ids) > 0:
			c['initital_bal'] = True
			sql = """SELECT COALESCE(SUM(CASE WHEN l2.debit > 0 THEN l2.debit ELSE 0 END),0.0), COALESCE(SUM(CASE WHEN l2.credit > 0 THEN l2.credit ELSE 0 END),0.0),COALESCE(SUM(CASE WHEN l2.amount_currency > 0 THEN l2.amount_currency ELSE l2.amount_currency END),0.0) 
				    FROM account_move_line l1 LEFT JOIN account_move_line l2
				    ON (l1.account_id = l2.account_id
				      AND l2.id <= l1.id
				      AND """ + \
				account_pool._query_get(cr, uid, obj='l2', context=c) + \
				") WHERE l1.date >= '"+date_from+"' and l1.date  <= '"+date_to+"'  AND l1.id IN %s GROUP BY l1.id ORDER BY l1.id DESC LIMIT 1"
			cr.execute(sql, [tuple(ids)])
			c = cr.fetchall()
			lines=[]
			for f in c:
				res={}
				res.update({'debit' : f[0]})
				res.update({'credit' : f[1]})
				res.update({'amount_curr' : f[2]})
				lines.append(res)
			return lines
		else:
			return False

	def ae_update_sequence(self,cr, uid, ids, journal_id, doc_type, context=None):
		if journal_id:
			journa_obj = self.pool.get('account.journal')
			diario = journa_obj.browse(cr,uid,journa_obj.search(cr,uid,[('id','=',journal_id)],context=None),context=context)
			fl=False
			if diario.sequence_id.id:
				cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (diario.sequence_id.id,))
			
		else:
			raise osv.except_osv(_('Error !'),_("Could't update the sequence for this journal!"))

	
	def recalculate(self, cr, uid, ids, context=None):
		context = dict(context or {})
		actual_obj = self.browse(cr, uid , ids, context = context)
		acc_ids=[]
		accounts = None
		ex_pool = self.pool.get('account.exchange.difference')
		actual_obj = self.browse(cr, uid, ids, context=context)
		account_pool = self.pool.get('account.account')
		for i in actual_obj.lines_ids:
			if i.account_id.currency_id:
				acc_ids.append(i.account_id.id)
		dummy, view_id_form  = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'innova_account_plus', 'account_plus_exchange_wizard_form')
		context.update({'reccal' : True})
		context.update({'id_exchdif':actual_obj.id})
		context.update({'date_to':actual_obj.date})
		context.update({'comm':actual_obj.comment})
		context.update({'date_from':actual_obj.date_from})
		context.update({'journal_id':actual_obj.journal_id.id})
		context.update({'currency_id':actual_obj.currency_id.id})
		context.update({'account_ids':acc_ids})
		
		return {
			'name':_("Exchange Diference Recalcullation"),
			'view_type': 'form',
			'view_mode': 'form',
		   	'res_model': 'exchange_diff_wizard',
		    	'type': 'ir.actions.act_window',
			'context': context,
			'views': [(view_id_form,'form')],
			'nodestroy': True,
		    	'target': 'new',
		}
	
	def validate(self, cr, uid, ids, context=None):
		arg=None
		context = dict(context or {})
		actual_objct = self.browse(cr, uid, ids, context=context)
		if not (actual_objct.journal_id and actual_objct.date_from and actual_objct.date):
			raise osv.except_osv(_('Error!'),_("There are some required fields with null values"))
		number = None
		value = 0
		value_today=0
		diff=0
		b = None
		number = '/'
		values_act={}
		ir_seq_pool = self.pool.get('ir.sequence')
		decimal_precision = self.pool.get('decimal.precision')
		dec_prec = decimal_precision.browse(cr,uid,decimal_precision.search(cr,uid,[('name' , '=', 'Account' )],context=None),context=context)
		period_pool = self.pool.get('account.period')
		model_user = self.pool.get('res.users')
		journal_pool= self.pool.get('account.journal')
		obj_user = model_user.browse(cr,uid,model_user.search(cr,uid,[('id' , '=', uid )],context=None),context=context)
		model_company = self.pool.get('res.company')
		obj_company = model_company.browse(cr,uid,model_company.search(cr,uid,[('id' , '=', obj_user.company_id.id )],context=None),context=context)
		period_ids = period_pool.find(cr,uid,actual_objct.date,  context=context)
		amove_obj= self.pool.get('account.move')
		amovedata={}
		journal = actual_objct.journal_id
		from_curr_obj = actual_objct.currency_id.with_context(date=actual_objct.date)
		to_curr_obj = obj_company.currency_id.with_context(date=actual_objct.date)
		inverse_factor = from_curr_obj.rate/to_curr_obj.rate
		if actual_objct.was_unreconcilied:
			number = number or '/'
		else:
			number = ir_seq_pool.journal_number(cr,uid,ids,actual_objct.journal_id.id,'exch_diff',context=None)
		
		for period_obj in period_ids:
			period_id = period_obj
		amovedata['journal_id']=journal.id
		amovedata['name'] = number or '/'
		amovedata['date'] = datetime.now()
		amovedata['period_id'] = period_id
		amovedata['ref'] = number
		move_id = amove_obj.create(cr,uid,amovedata,context=context)
		if move_id:
			values_act.update({'move_id': move_id})
		else:
			raise osv.except_osv(_('Error!'),_("The Operation was not finished"))
		mline_obj= self.pool.get('account.move.line')
		lines_array=[]
		for lineas in actual_objct.lines_ids:
			lines_col={}
			lines_col['move_id'] = move_id
			lines_col['ref'] = number or '/'
			lines_col['name'] = actual_objct.comment or '/'
			lines_col['currency_id'] =actual_objct.currency_id.id
			lines_col['date'] = actual_objct.date
			lines_col['amount_currency'] = None
			lines_col['account_id'] = lineas.account_id.id#gain
			amoun_curr_value = None
			if lineas.debit not in [None,False,0]:
				lines_col['credit'] = None
				lines_col['debit'] = lineas.debit
				amoun_curr_value = lineas.debit
			else:
				lines_col['credit'] = lineas.credit
				lines_col['debit'] = None
				amoun_curr_value = (-1)*lineas.credit
			lines_array.append(lines_col)#adding movline to an array
			
		for linea in lines_array:
			mline_obj.create(cr,uid,linea)
		values_act.update({'state':'validated'})
		self.ae_update_sequence(cr, uid, ids, actual_objct.journal_id.id, 'exch_diff', context=None)
		amove_obj.post(cr, uid, [move_id], context={})
		self.write(cr, uid, ids,values_act, context=context)		


	def _get_lines(self, cr, uid, ids,field, arg,  context=None):
		res={}
		objs = self.browse(cr, uid, ids, context=context)
		lines={}
		mline_pool= self.pool.get('account.move.line')
		for obj in objs:
			move_line_obj = mline_pool.browse(cr, uid, mline_pool.search(cr, uid, [('move_id','=',obj.move_id.id)], context=context), context=context)
			res[obj.id]= move_line_obj
		return res
	
	def create(self, cr, uid, values, context=None):
		values['state'] = 'draft'
		b = super(account_exchange_validate, self).create(cr, uid, values, context=context)
		if b:
			return b
		else:
			return False
				
		
	def unlink(self, cr, uid, ids, context=None):
		flag=False
		for mc in self.browse(cr, uid, ids, context=context):
			if mc.state in  ['draft'] or  mc.was_unreconcilied:
				flag=True
		if not flag:
			raise osv.except_osv(_('Error!'),_("You can not delete this file when it has a diferent state than Draft !"))
		else:	
			return super(account_exchange_validate, self).unlink(cr, uid, ids, context=context)
	def _get_number_name(self, cr, uid, ids,field, arg,  context=None):
		res={}
		objs = self.browse(cr, uid, ids, context=context)
		for obj in objs:
			res[obj.id]= obj.number
		return res
	def  gain_account(self, cr, uid, context=None):
		user_pool=self.pool.get('res.users')
		user=user_pool.browse(cr,uid,uid,context=context)
		if user.company_id.expense_currency_exchange_account_id:
			return user.company_id.income_currency_exchange_account_id.id
		else:	
			return False
	def  lost_account(self, cr, uid, context=None):
		user_pool=self.pool.get('res.users')
		user=user_pool.browse(cr,uid,uid,context=context)
		if user.company_id.expense_currency_exchange_account_id:
			return user.company_id.expense_currency_exchange_account_id.id
		else:	
			return False
	_columns = {
		'name' : fields.function(_get_number_name,type='char',string='name'),
        	'number':fields.char('Number', copy=False),
		'date_from':fields.date('From',  select=True ,required=False ),
		'date':fields.date('To',  select=True, ),
		'currency_id' : fields.many2one('res.currency', 'Currency', copy=False),
		'rate' : fields.float( string='rate',),
		'journal_id':fields.many2one('account.journal', 'Journal',required=False ),
		'comment': fields.char('Comment'),
		'move_id':fields.many2one('account.move', 'Account Entry', copy=False),
		'move_lines':fields.function( _get_lines,type='one2many',string='Total',relation='account.move.line', copy=False),
		'lines_ids' :fields.one2many('account.exchange.difference.lines','aed_id',string="lines", track_visibility='onchange'),
		'was_unreconcilied': fields.boolean(string='Unreconcilied'),
		'gain': fields.float( string='Gain',),
		'lost': fields.float( string='Lost',),
		'gain_account' : fields.many2one('account.account', 'Gain Account'),
		'lost_account' : fields.many2one('account.account', 'Lost Account'),
		'difference': fields.float( string='Difference',),
		'state':fields.selection(
		    [('draft','Draft'),
		     ('validated','Validated'),
		    ], 'Status',track_visibility='onchange',)
	}
		#'temporal_code': fields.char(string='Temporal Code',),
	_defaults = {
		'gain_account' : gain_account,
		'lost_account' : lost_account,
		    } 



class account_exchange_validate_lines(osv.Model):

    
    	_name = 'account.exchange.difference.lines'
	
	_columns = {
        	'ref':fields.char('ref'),
		'account_id' : fields.many2one('account.account', 'Account'),
		'amount_forg_curr': fields.float('amount(forg)'),
		'amount_local_curr' : fields.float('amount(local)'),
		'calculated_amount': fields.float('amount'),
		'debit': fields.float('debit'),
		'credit':fields.float('credit'),
		'aed_id':fields.many2one('account.exchange.difference', 'Lines'),
	}


