# -*- coding: utf-8 -*-

import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import api
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
from datetime import datetime,timedelta
class exchange_diff(osv.osv_memory):
	_name = 'exchange_diff_wizard'
	
	
	def is_in_range(self, cr, uid, ids,date_from,date_to, context = None):
		exchanga_pool = self.pool.get('account.exchange.difference')
		exch_obj = exchanga_pool.browse(cr, uid,exchanga_pool.search(cr, uid, [],context=context),context=context)
		if exch_obj:
			for exch in exch_obj:
				if exch.date_from not in [False,None] or exch.date not in [False,None]:
					if (date_from >= exch.date_from and date_from <= exch.date ) or (date_to >= exch.date_from and date_to <= exch.date ):
						return True
		return False

	def get_last_exhan_cal(self, cr, uid, ids,currency_id,date_to, context = None):
		sql="SELECT aed.date FROM account_exchange_difference AS aed WHERE aed.state = 'validated'  AND aed.currency_id = "+str(currency_id)+" ORDER BY aed.date DESC LIMIT 1"
		cr.execute(sql)
		res = cr.fetchone()
		if res not in [None,False]:
			return datetime.strptime(res[0],'%Y-%m-%d') + timedelta(days=1)
		else:
			fy = self.pool.get('account.fiscalyear')
			fy1 = fy.browse(cr, uid, fy.search(cr, uid, [('date_start', '<=' ,date_to),('date_stop', '>=', date_to),('state', '=', 'draft')], context=context),context=context)
			if fy1:			
				return datetime.strptime(fy1.date_start,'%Y-%m-%d')
			else:
				raise osv.except_osv(_('Error!'),_("Selected date do not belong to an open period!"))

	def buscar_post_lines(self, cr, uid, ids, account_id, context=None):
		cr.execute("SELECT count(id) FROM account_move_line aml WHERE aml.state = 'draft' AND aml.account_id = "+ str(account_id) )
		c = cr.fetchone() 
		if c  != None and c != False:
			if len(c) > 0:
				return True
		return False

	def get_balance_per_account(self, cr, uid, ids,account_pool,date_from,date_to, context=None):
		if context is None:
			context = {}
		c = context.copy()
		if len(ids) > 0:
			c['initital_bal'] = True
			sql = """SELECT COALESCE(SUM(CASE WHEN l1.debit > 0 THEN l1.debit ELSE 0 END),0.0), COALESCE(SUM(CASE WHEN l1.credit > 0 THEN l1.credit ELSE 0 END),0.0),COALESCE(SUM(CASE WHEN l1.amount_currency > 0 THEN l1.amount_currency ELSE l1.amount_currency END),0.0) 
				    FROM account_move_line l1 
					 WHERE  """ + \
				account_pool._query_get(cr, uid, obj='l1', context=c) + \
				"  AND l1.state <> 'draft' AND l1.date >= '"+str(date_from)+"' and l1.date  <= '"+str(date_to)+"' AND l1.id IN %s"
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
	def load_exh_model(self, cr, uid, ids, context=None):
		b=None
		model_user = self.pool.get('res.users')
		obj_user = model_user.browse(cr,uid,model_user.search(cr,uid,[('id' , '=', uid )],context=None),context=context)
		account_pool = self.pool.get('account.account')
		model_company = self.pool.get('res.company')
		ir_seq_pool = self.pool.get('ir.sequence')
		journal_pool= self.pool.get('account.journal')
		context = dict(context or {})
		date_from = self.get_last_exhan_cal(cr, uid, ids,context.get('currency',False),context.get('today_date',False), context = context)
		obj_company = model_company.browse(cr,uid,model_company.search(cr,uid,[('id' , '=', obj_user.company_id.id )],context=None),context=context)
		curr_pool = self.pool.get('res.currency')
		actual_currency = curr_pool.browse(cr, uid, context.get('currency',False),context=context)
		from_curr_obj = actual_currency.with_context(date=context.get('today_date',False))
		to_curr_obj = obj_company.currency_id.with_context(date=context.get('today_date',False))
		if context.get('last_date',False) and context.get('today_date',False) and context.get('currency',False) and context.get('rate',False) and context.get('journal',False):	
			if self.is_in_range( cr, uid, ids,context.get('last_date',False),context.get('today_date',False), context = context) and (context.get('reccal') == False):
				raise osv.except_osv(_('Error!'),_("There is a date that is already in a range"))
			if obj_company.currency_id.id == context.get('currency',False):
				raise osv.except_osv(_('Error!'),_("This currency is the same of your company"))
			
			exchange_dif = {}
			exchanga_pool = self.pool.get('account.exchange.difference')
			exchange_dif['number'] = ir_seq_pool.journal_number(cr,uid,ids,context.get('journal',False),'exch_diff',context=None)
			exchange_dif['date'] = context.get('today_date',False)
			exchange_dif['journal_id'] = context.get('journal',False)
			exchange_dif['comment'] = context.get('comment',False)
			exchange_dif['currency_id'] = context.get('currency',False)
			exchange_dif['date_from'] =  date_from
			exchange_dif['rate'] =  to_curr_obj .rate
			if context.get('reccal') == False:
				b = exchanga_pool.create(cr, uid, exchange_dif, context = context)
				exchanga_pool.write(cr, uid, b,{'state':'draft'},context=context)
			else:
				b =  context.get('id_exchdif',False)
				exch_lines_pool = self.pool.get('account.exchange.difference.lines')
				exch_lines_pool.unlink(cr,uid,exch_lines_pool.search(cr,uid,[('aed_id','=',b)],context=context),context=context)
				exchange_dif['lines_ids'] = False
				exchanga_pool.write(cr, uid,b ,exchange_dif,context=context)
			decimal_precision = self.pool.get('decimal.precision')
			dec_prec = decimal_precision.browse(cr,uid,decimal_precision.search(cr,uid,[('name' , '=', 'Account' )],context=None),context=context)
			exchanga_line_pool = self.pool.get('account.exchange.difference.lines')
			lines_array=[]
			accounts_count = 0
			accounts_obj = self.browse(cr, uid, ids, context=context).account_ids
			if context.get('all_accounts') == True:
				accounts_obj = account_pool.browse(cr, uid,account_pool.search(cr, uid,[('currency_id','=',context.get('currency',-1))],context=context),context=context)
			accounts_count = len(accounts_obj)
			if accounts_count <= 0:
				raise osv.except_osv(_('Warning!'),_("Select at least one account!"))
			zero_accounts = 0
			rate_factor = to_curr_obj.rate/from_curr_obj.rate
			rate_factor_inv = from_curr_obj.rate/to_curr_obj.rate
			tot_gain = 0
			tot_lost = 0
			tot_difference = 0
			for accounts in accounts_obj:
				if self.buscar_post_lines(cr, uid ,ids, accounts.id ,context=context):
					value = 0
					value_today = 0
					amou_curr=0
					diff = 0
					account_pool =  self.pool.get('account.move.line')
					line_ids =  account_pool.search(cr, uid, [('account_id','=',accounts.id),('state','=','valid')],context=context)
					x = self.get_balance_per_account( cr, uid,line_ids ,account_pool, date_from,context.get('today_date',False), context=context)
					if  x is  False and x is  None:
						raise osv.except_osv(_('Error!'),_("Ther was a problem, please try again!"))
					if x:
						for val in x:
							value += round((val['debit']-val['credit']), dec_prec.digits)
							amou_curr += round(val['amount_curr'], dec_prec.digits)
						value_today = round(amou_curr*rate_factor,dec_prec.digits)
						diff = round((value - value_today),dec_prec.digits)
						
					if diff != 0:
						for i in [1,2]:
							exchange_dif_lines = {}
							exchange_dif_lines['ref'] = context.get('comment',False) or '/'
							exchange_dif_lines['aed_id'] = b
							exchange_dif_lines['amount_forg_curr'] = amou_curr
							exchange_dif_lines['amount_local_curr'] = value
							exchange_dif_lines['calculated_amount'] = value_today
							diff = abs(diff)
							if i == 1:
								if value < value_today:
									exchange_dif_lines['credit'] = diff
									exchange_dif_lines['debit'] = 0
									exchange_dif_lines['account_id'] = obj_company.income_currency_exchange_account_id.id#gain
									tot_gain =+  diff
								else:
									exchange_dif_lines['credit'] = 0
									exchange_dif_lines['debit']  = diff
									exchange_dif_lines['account_id'] = obj_company.expense_currency_exchange_account_id.id#loss
									tot_lost += diff
							else:
								exchange_dif_lines['account_id'] = accounts.id#gain
								if value < value_today:
									exchange_dif_lines['credit'] = 0
									exchange_dif_lines['debit'] = diff
								else:
									exchange_dif_lines['credit'] = diff
									exchange_dif_lines['debit'] = 0
							lines_array.append(exchange_dif_lines)#adding movline to an array
					else:
						zero_accounts+=1
			exchanga_pool.write(cr, uid, b,{'gain':tot_gain, 'lost':tot_lost, 'difference':(tot_gain+tot_lost)},context=context)
			for linea in lines_array:
				exchanga_line_pool.create(cr,uid,linea)
			#------------------------------------------------------------------------------------------------------------------------------------
			dummy, view_id_tree  = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'innova_account_plus', 'view_account_exchange_difference_tree')
			dummy, view_id_form  = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'innova_account_plus', 'view_account_account_exchange_difference_form')
			if not ids: return []
			if zero_accounts == accounts_count:
				raise osv.except_osv(_('Message!'),_("None of the accounst with the secundary currency "+actual_currency.name+" has an exchange difference value"))
			return {
				'name':_("Exchange Diference"),
				'view_type': 'form',
			   	'res_model': 'account.exchange.difference',
			    	'type': 'ir.actions.act_window',
				'context': context,
				'views': [(view_id_form,'form'),(view_id_tree, 'tree')],
				'res_id' : b,
				'nodestroy': True,
			    	'target': 'current',
			    	'domain': '[]'
				}

	'''def onchange_last_date(self, cr, uid, ids,date_from,date_to, context=None):
		fisy = self.get_fiscal_year(cr, uid, ids, date_from , date_to, context = context)
		values={}
		values = dict(values or {})
		if fisy['is_int'] in [False,None]:
			values.update({ 'msg' : fisy['value'], 'last_procces_date': None,'last_procces_date_calc': None})
		else:
			values.update({ 'msg' : None})
		return {'value' : values}'''

	def onchange_rate(self, cr, uid, ids, currency_id,date_to, context=None):
		if currency_id and date_to:
			res={}
			values={}
			values = dict(values or {})
			currency_pool = self.pool.get('res.currency')
			currency_obj = currency_pool.browse(cr, uid, currency_id, context=context)
			currency = self.get_current_rate(cr, uid,[ currency_obj.id] , date_to, False, context=context)
			c =  self.get_last_exhan_cal(cr, uid, ids,currency_id,date_to, context = context)
			if currency:
				values.update({ 'rate' : currency['rate'],  'rate_calc' : currency['rate']})
			if c not in [False,None]:
				if c >  datetime.strptime(date_to,'%Y-%m-%d'):
					values.update({ 'last_procces_date':None,'last_procces_date_calc':None,'msg': "Dates conflict, 'initial date' = "+str(c)+" and 'final date'="+str(date_to)+"!!", 'rate' : None})
				else:
					values.update({ 'last_procces_date' : c,'last_procces_date_calc': c, 'msg' : False})
			else:
				values.update({ 'last_procces_date' : None,'msg': 'This date do not belong to an open period!!','rate' : None})
			return {'value' : values}
		else:
			return {'value' : {}}

	def get_current_rate(self, cr, uid, ids, date_now, raise_on_no_rate=True, context=None):
		if context is None:
            		context = {}
       		res = {}
       		date = date_now or time.strftime('%Y-%m-%d')
       		for id in ids:
		    	cr.execute('SELECT rate FROM res_currency_rate '
		               'WHERE currency_id = %s '
		                 'AND name <= %s '
		               'ORDER BY name desc LIMIT 1',
		               (id, date))
		    	if cr.rowcount:
		        	res['rate'] = cr.fetchone()[0]
		   	elif not raise_on_no_rate:
		        	res['rate'] = 0
		    	else:
		        	currency = self.browse(cr, uid, id, context=context)
		        	raise osv.except_osv(_('Error!'),_("No currency rate associated for currency '%s' for the given period" % (currency.name)))
        	return res
	
	@api.constrains('today_date')
	def _constraint(self):
    		for record in self:
        		if record.last_procces_date >  record.today_date:
            			raise ValidationError("Error!! 'From date' has to be greater than 'To date'")
	_columns = {
		'msg': fields.char(string='char'),
		'last_procces_date':fields.date('From',  select=True ,required=True ),
		'last_procces_date_calc':fields.date('From',  select=True ,required=False,store=False),
		'comment':fields.char(string="Comment",  select=True, help=_("Comment"),required=False ),
		'journal_id':fields.many2one('account.journal', 'Journal',select=True,required=True ),
		'account_ids': fields.many2many('account.account',required=False ),
		'today_date':fields.date('Date',  select=True, help=_("Last Procces Date"),required=False ),
		'currency':fields.many2one('res.currency',string="Currency",  select=True, help=_("Currency to evaluate"),required=True ),
		'rate':fields.float(string="Rate",  select=True, help=_("Rate"),required=True ),
		'rate_calc':fields.float(string="Rate",  select=True, help=_("Rate"),required=False,store=False ),
		'all_accounts':fields.boolean(string="Use all accounts",store=False ),
	}
	_order = 'today_date desc'
	
	_defaults = {
		'today_date': lambda self, cr, uid, context: context['date_to'] if context and  context['date_to'] not in [False,None] else  time.strftime('%Y-%m-%d'),
		'journal_id': lambda self, cr, uid, context: context['journal_id'] if context and  context['journal_id'] not in [False,None] else  False,
		'currency': lambda self, cr, uid, context: context['currency_id'] if context and  context['currency_id'] not in [False,None] else  False,
		'comment': lambda self, cr, uid, context: context['comm'] if context and  context['comm'] not in [False,None] else  False,
		'last_procces_date': lambda self, cr, uid, context: context['date_from'] if context and  context['date_from'] not in [False,None] else  False,
		'account_ids' : lambda self, cr, uid, context: context['account_ids'] if context and  context['account_ids'] not in [False,None] else  False,
		 } 
