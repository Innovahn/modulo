# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import models, api
from datetime import datetime
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class ap_account_voucher_line(osv.Model):

	_inherit = 'account.voucher'

	def _get_amount_copy(self,cr, uid, ids, field, arg, context=None):
		result={}
		for v in self.browse(cr,uid,ids,context=context):
			result[v.id]=v.writeoff_amount
		return result
	_columns = {
		'amount_if_exch':fields.float(string="Value if Exchange",required=False),
		'retention_lines':fields.one2many('retention.lines','voucher_id',string="Retention lines",required=False),
		'retention_ref' : fields.many2one('retentions','Retention Payment',required=False),
		'dif_ret_writeamount' : fields.float('Difference',compute='_compute_writteamount_diff', digits_compute=dp.get_precision('Account')),
		'writeoff_amount_copy' : fields.function(_get_amount_copy,type='float',string='Difference amount',),
		'payment_option':fields.selection([
                                           ('without_writeoff', 'Keep Open'),
                                           ('with_writeoff', 'Reconcile Payment Balance'),
					    ('retention_lines', 'Retention lines'),
                                           ], 'Payment Difference', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the payment(s)"),
       
		}
	def load_reten_wizard(self, cr, uid, ids, context=None):
		dummy, view_id_form  = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'innova_account_plus', 'retention_lines_assig_wizard_form')
		if not ids: return []
		act_voucher = self.browse(cr, uid, ids, context=context)
		context=dict(context or {})
		line_ids=[]
		context.update({'voucher_id': act_voucher.id})
		context.update({'mcheck_id': None})
		for aid in act_voucher.retention_lines:
			line_ids.append(aid.id)
		if len(line_ids)>0:
			context.update({'retentions_lines':line_ids})
		return {
			'name':_("Exchange Diference"),
			'view_type': 'form',
		   	'res_model': 'retention_lines_assig_wizard',
		    	'type': 'ir.actions.act_window',
			'context': context,
			'views': [(view_id_form, 'form')],
			'nodestroy': True,
		    	'target': 'new',
		    	'domain': '[]'
			}


	@api.one
   	@api.depends('writeoff_amount')
	def _compute_writteamount_copy(self):
		self.writeoff_amount_copy =  self.writeoff_amount #super(ap_account_voucher_line,self)._compute_writeoff_amount(self.cr, self.uid, self.line_dr_ids, self.line_cr_ids, self.amount, self.type)
	@api.one
   	@api.depends('retention_lines')
	def _compute_writteamount_diff(self):
		tot_line=0
		for line in self.retention_lines:
			tot_line+=line.amount
		self.dif_ret_writeamount = abs(self.writeoff_amount) - tot_line

	def get_date_last_exch_diff(self,cr, uid, ids,date,account_id,currency_id, context=None):
		sql = "SELECT aed.date FROM account_exchange_difference AS aed WHERE aed.state = 'validated'  AND aed.currency_id = "+str(currency_id)+" AND aed.id IN (SELECT aefl.aed_id FROM account_exchange_difference_lines as aefl WHERE aefl.account_id = "+str(account_id)+") ORDER BY aed.date DESC LIMIT 1"
		cr.execute(sql)
		res = cr.fetchone()
		if res not in [None,False]:
			return datetime.strptime(res[0],'%Y-%m-%d') #+ timedelta(days=1)
		else:
			return False
	def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
		if not ids: return {}
		currency_obj = self.pool.get('res.currency')
		res = {}
		debit = credit = 0.0
		for voucher in self.browse(cr, uid, ids, context=context):
		    	sign = voucher.type == 'payment' and -1 or 1
		    	for l in voucher.line_dr_ids:
		        	debit += l.amount
		    	for l in voucher.line_cr_ids:
		       		credit += l.amount
		    	currency = voucher.currency_id or voucher.company_id.currency_id
		    	res[voucher.id] =  currency_obj.round(cr, uid, currency, voucher.amount - sign * (credit - debit))
		return res

	def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
		'''
		Create one account move line, on the given account move, per voucher line where amount is not 0.0.
		It returns Tuple with tot_line what is total of difference between debit and credit and
		a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

		:param voucher_id: Voucher id what we are working with
		:param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
		:param move_id: Account move wher those lines will be joined.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
		:rtype: tuple(float, list of int)
		'''
		if context is None:
			context = {}
		move_line_obj = self.pool.get('account.move.line')
		currency_obj = self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		tot_line = line_total
		rec_lst_ids = []
		date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
		ctx = context.copy()
		ctx.update({'date': date})
		voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
		voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
		ctx.update({
		    	'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
		    	'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
		prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
		for line in voucher.line_ids:
			#create one move line per voucher line where amount is not 0.0
		    	# AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
		    	if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
				continue
			# convert the amount set on the voucher line into the currency of the voucher's company
		    	# this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
			amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
			# if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
		    	# currency rate difference
			#addeed lines by innovaacccountplus
		    	new_amount_res=0
		    	flag=False
			new_value = 0 #importanteeeeeeeeeeeeeeeeeeee
			from_curr_obj = voucher.currency_id.with_context(date=line.move_line_id.date)
		    	date_last_exch_diff = self.get_date_last_exch_diff(cr, uid, voucher_id,line.move_line_id.date,line.account_id.id,line.currency_id.id, context=context)#use the account
			if date_last_exch_diff:
				if line.move_line_id.date <= datetime.strftime(date_last_exch_diff,'%Y-%m-%d'): #or date_maturity
					from_curr_obj = voucher.currency_id.with_context(date=date_last_exch_diff)
					to_curr_obj = voucher.company_id.currency_id.with_context(date=date_last_exch_diff)
					flag = True
					sign1 = 1
					if line.move_line_id.currency_id:
						sign1 = line.move_line_id.amount_currency < 0 and -1 or 1
					else:
						sign1 = (line.move_line_id.debit - line.move_line_id.credit) < 0 and -1 or 1
					new_amount_res = sign1*line.amount * (to_curr_obj.rate/from_curr_obj.rate)
					new_amount_res = new_amount_res < 0 and -new_amount_res or new_amount_res 
					new_value = new_amount_res
					self.pool.get('account.voucher').write(cr, uid,voucher.id,{'amount_if_exch': new_amount_res},context=context)
		    	if line.amount == line.amount_unreconciled:
		        	if not line.move_line_id:
		            		raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
		        	sign = line.type =='dr' and -1 or 1
				if not flag:#added line
					currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
		        	else:
		            		currency_rate_difference = sign * ( new_amount_res - amount)
				
		    	else:
		        	currency_rate_difference = 0.0
		    
			move_line = {
				'journal_id': voucher.journal_id.id,
				'period_id': voucher.period_id.id,
				'name': line.name or '/',
				'account_id': line.account_id.id,
				'move_id': move_id,
				'partner_id': voucher.partner_id.id,
				'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
				'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
				'quantity': 1,
				'credit': 0.0,
				'debit': 0.0,
				'date': voucher.date
			}
		    	if amount < 0:
		        	amount = -amount
		        	if line.type == 'dr':
		            		line.type = 'cr'
		        	else:
		            		line.type = 'dr'

		    	if (line.type=='dr'):
		        	tot_line += amount
		        	move_line['debit'] = amount
		    	else:
		        	tot_line -= amount
		        	move_line['credit'] = amount

		    	if voucher.tax_id and voucher.type in ('sale', 'purchase'):
		       		move_line.update({
		            	'account_tax_id': voucher.tax_id.id,
		        	})

		    	# compute the amount in foreign currency
		    	foreign_currency_diff = 0.0
		    	amount_currency = False
		    	if line.move_line_id:
		        	# We want to set it on the account move line as soon as the original line had a foreign currency
		        	if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
		            		# we compute the amount in that foreign currency.
		            		if line.move_line_id.currency_id.id == current_currency:
		                		# if the voucher and the voucher line share the same currency, there is no computation to do
		                		sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
		                		amount_currency = sign * (line.amount)
		            		else:
		                		# if the rate is specified on the voucher, it will be used thanks to the special keys in the context
		                		# otherwise we use the rates of the system
		                		amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
		        	if line.amount == line.amount_unreconciled:
		            		foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)
			move_line['amount_currency'] = amount_currency
		   	voucher_line = move_line_obj.create(cr, uid, move_line)
		    	rec_ids = [voucher_line, line.move_line_id.id]

		    	if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
		       		# Change difference entry in company currency
		        	exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
				new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
		        	move_line_obj.create(cr, uid, exch_lines[1], context)
		        	rec_ids.append(new_id)

		    	if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
		        	# Change difference entry in voucher currency
		        	move_line_foreign_currency = {
				    'journal_id': line.voucher_id.journal_id.id,
				    'period_id': line.voucher_id.period_id.id,
				    'name': _('change')+': '+(line.name or '/'),
				    'account_id': line.account_id.id,
				    'move_id': move_id,
				    'partner_id': line.voucher_id.partner_id.id,
				    'currency_id': line.move_line_id.currency_id.id,
				    'amount_currency': -1 * foreign_currency_diff,
				    'quantity': 1,
				    'credit': 0.0,
				    'debit': 0.0,
				    'date': line.voucher_id.date,
		        	}
				new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
		        	rec_ids.append(new_id)
		    	if line.move_line_id.id:
		        	rec_lst_ids.append(rec_ids)
       		return (tot_line, rec_lst_ids)

	def voucher_retention_lines_total(self, cr, uid, ids, context = None):
		voucher = self.pool.get('account.voucher').browse(cr,uid,ids,context)
		tot = 0
		if voucher.retention_lines:
			for line in voucher.retention_lines:
				tot+=line.amount
			if abs(tot) != abs(voucher.writeoff_amount):
				raise osv.except_osv(_('Error'),_("The sum of retentions lines amount is diferent than writtof amount"))
			return tot
		else:
			return False
	def action_move_line_create(self, cr, uid, ids, context=None):
		'''
		Confirm the vouchers given in ids and create the journal entries for each of them
		'''
		if context is None:
		    context = {}
		move_pool = self.pool.get('account.move')
		move_line_pool = self.pool.get('account.move.line')
		for voucher in self.browse(cr, uid, ids, context=context):
		    local_context = dict(context, force_company=voucher.journal_id.company_id.id)
		    if voucher.move_id:
			continue
		    company_currency = self._get_company_currency(cr, uid, voucher.id, context)
		    current_currency = self._get_current_currency(cr, uid, voucher.id, context)
		    # we select the context to use accordingly if it's a multicurrency case or not
		    context = self._sel_context(cr, uid, voucher.id, context)
		    # But for the operations made by _convert_amount, we always need to give the date in the context
		    ctx = context.copy()
		    ctx.update({'date': voucher.date})
		    # Create the account move record.
		    move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
		    # Get the name of the account_move just created
		    name = move_pool.browse(cr, uid, move_id, context=context).name
		    # Create the first line of the voucher
		    move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
		    move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
		    line_total = move_line_brw.debit - move_line_brw.credit
		    rec_list_ids = []
		    if voucher.type == 'sale':
		        line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
		    elif voucher.type == 'purchase':
		        line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
		    # Create one move line per voucher line where amount is not 0.0
		    line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context = context)

		    # Create the writeoff line if needed
		    ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
		    if ml_writeoff:
		        move_line_pool.create(cr, uid, ml_writeoff, local_context)
		    # We post the voucher.
		    self.write(cr, uid, [voucher.id], {
		        'move_id': move_id,
		        'state': 'posted',
		        'number': name,
		    })
		    if voucher.journal_id.entry_posted:
		        move_pool.post(cr, uid, [move_id], context={})
		    # We automatically reconcile the account move lines.
		    reconcile = False
		    for rec_ids in rec_list_ids:
		        if len(rec_ids) >= 2:
			    if voucher.amount_if_exch not in [False,None,0]:
				context['new_value'] = voucher.amount_if_exch
    				context['voucher_id'] = voucher.id
		            reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id,context = context)
		return True
	
	
	def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
		'''
		Set a dict to be use to create the writeoff move line.

		:param voucher_id: Id of voucher what we are creating account_move.
		:param line_total: Amount remaining to be allocated on lines.
		:param move_id: Id of account move where this line will be added.
		:param name: Description of account move line.
		:param company_currency: id of currency of the company to which the voucher belong
		:param current_currency: id of currency of the voucher
		:return: mapping between fieldname and value of account move line to create
		:rtype: dict
		'''
		currency_obj = self.pool.get('res.currency')
		move_line = {}
		context = dict(context or {})
		voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
		current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id
		if not context.get('recur_call',False):#added bifurcation
			tot_lines = self.voucher_retention_lines_total( cr, uid, voucher_id, context=context)## added line
			if tot_lines:
				move_line_pool = self.pool.get('account.move.line')
				lines_array = []
				for line in voucher.retention_lines:
					new_line=None
					context.update({'recur_call' : True})
					context.update({'rl_account_id' : line.account_id.id})
					line_amount = 0
					sign = voucher.type == 'payment' and -1 or 1
					line_amount = voucher.writeoff_amount > 0 and sign*(abs(line.amount)) or sign*(-1)*(abs(line.amount))
					new_line = self.writeoff_move_line_get(cr, uid, voucher_id, line_amount, move_id, line.description, company_currency, current_currency, context=context)
					lines_array.append(new_line)
				for l in lines_array:
					nid=move_line_pool.create(cr, uid, l, context)
				return False
			
        	if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
			    diff = line_total
			    account_id = False
			    write_off_name = ''
			    if voucher.payment_option == 'with_writeoff':
					account_id = voucher.writeoff_acc_id.id
					write_off_name = voucher.comment
			    elif voucher.partner_id:
					if voucher.type in ('sale', 'receipt'):
				    		account_id = voucher.partner_id.property_account_receivable.id
					else:
				    		account_id = voucher.partner_id.property_account_payable.id
			    else:
					# fallback on account of voucher
					account_id = voucher.account_id.id
		    	    sign = voucher.type == 'payment' and -1 or 1
		    	    move_line = {
			    'name': write_off_name or name,
			    'account_id': account_id, 
			    'move_id': move_id,
			    'partner_id': voucher.partner_id.id,
		            'date': voucher.date,
			    'credit': diff > 0 and diff or 0.0,
			    'debit': diff < 0 and -diff or 0.0,
			    'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or 0.0,
			    'currency_id': company_currency <> current_currency and current_currency or False,
			    'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
			    }
			    if context.get('recur_call',False):
			            move_line = dict(move_line or {})
				    account_id = account_id,
				    sign = voucher.type == 'payment' and -1 or 1
				    move_line.update({'account_id' : context.get('rl_account_id',False)})
				    #wamount = voucher.writeoff_amount > 0 and (abs(diff)) or -1*(abs(diff))
				    move_line.update({'amount_currency' : company_currency <> current_currency and (sign * -1 * diff* sign) or 0.0})
				    context = self._sel_context(cr, uid, voucher.id, context)
				    ctx = context.copy()
        	   	 	    ctx.update({'date': voucher.date})
				    value=self._convert_amount(cr, uid, diff, voucher.id, context=ctx)
				    move_line.update({'debit' : value < 0 and -value or 0.0,})
				    move_line.update({'credit' : value > 0 and value or 0.0,})
		return move_line

