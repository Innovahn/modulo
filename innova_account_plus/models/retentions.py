# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from datetime import datetime
import locale
import pytz
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
class retentions(osv.osv):

	_name = 'retentions'

	def get_next_number(self, cr, uid, ids, context=None):
		pool_seq = self.pool.get('ir.sequence')
		ban=0
		seq_id=0
		seq_obj = pool_seq.browse(cr, uid, pool_seq.search(cr, uid,[('code','=','retentions')], context=context), context = context)
		if not seq_obj:
			raise osv.except_osv(_('Configuration Error!'),_("You have to create a sequence with the code 'retentions'"))	
		if len(seq_obj) > 1:
			for seq in seq_obj:
				ban+=1
				if ban==1:
					seq_id=seq.id
		else:
			seq_id=seq_obj.id
		number = pool_seq.next_by_id(cr, uid, seq_id,context=context)
		return  {'number' :  number, 'seq' : seq_id}

	def unlink(self, cr, uid, ids, context=None):
		raise osv.except_osv(_('Error!'),_("You can not delete a retention!"))
		

	def create(self, cr, uid, values, context=None):
		values = dict(values or {})
		number=0
		number=self.get_next_number(cr, uid, uid, context=context)
		if not values.get('company_id'):
			pool_user = self.pool.get('res.users')
			user_obj = pool_user.browse(cr, uid, uid, context=context)
			values.update({'company_id': user_obj.company_id.id, 'user_id' : user_obj.id })
		if not values.get('cai'):
			cai=0
			cai=self._get_cai(cr, uid, context=context)
			values.update({'cai': cai})
		if not values.get('number'):
			values.update({'number': number['number'], 'sequence_id' : number['seq']})
		b = super(retentions, self).create(cr, uid, values, context=context)
		if b:
			return b
		else:
			return False



	def addComa(self, snum ):
		s = snum;
		i = s.index('.') # Se busca la posición del punto decimal
		while i > 3:
			i = i - 3
			s = s[:i] +  ',' + s[i:]
		return s
	def _get_cai(self, cr, uid, context=None):
		pool_seq = self.pool.get('ir.sequence')
		ban=0
		seq_id=0
		seq_obj = pool_seq.browse(cr, uid, pool_seq.search(cr, uid,[('code','=','retentions')], context=context), context = context)
		if seq_obj in [False, None]:
			raise osv.except_osv(_('Configuration Error!'),_("You have to create a sequence with the code 'retentions'"))
		for sq in seq_obj:
			for cais in sq.fiscal_regime:
				if cais.selected:
				 	return cais.cai.id
		
	def _get_total(self, cr, uid, ids, field, arg, context=None):
		result = {}
		totalc=0
		for r in self.browse(cr,uid,ids,context=context):
			if len(r.retention_lines) > 0:
				for lines in r.retention_lines:
					totalc+=abs(lines.amount)
			result[r.id]=self.addComa('%.2f'%(totalc))
		return result

	def _get_totalt(self, cr, uid, ids, field, arg, context=None):
		result = {}
		total = 0
		for ret in self.browse(cr,uid,ids,context=context):
			for lines in ret.retention_lines:
					total+=abs(lines.amount)
			if ret.pay_number.journal_id.currency:
				a = self.to_word(total,ret.pay_number.journal_id.currency.name)
			else:
				a = self.to_word(total,'HNL')
			result[ret.id] = a
		return result	

	def _get_name(self, cr, uid, ids, field, arg, context=None):
		result = {}
		total=0
		for ret in self.browse(cr,uid,ids,context=context):
			if ret.number:
				result[ret.id]=ret.number
			else:
				result[ret.id] = 'Retention'
		return result	

	_columns = {
		'name' : fields.function(_get_name,type='char',string='Name',),
		'number' : fields.char('number',required = True),
		'date':fields.date('Date',required = True),
		'pay_number' : fields.many2one('account.voucher','Payment ref',required=False),
		'pay_number_check' : fields.many2one('mcheck.mcheck','Payment ref',required=False),
		'total_lines':fields.function(_get_total,type='char',string='Total',),
		'description': fields.char('Description',copy=False,required=False),
		'retention_lines' : fields.one2many('retention.lines','retention_id',required=True),
		'cai' : fields.many2one('dei.cai',string='Cai',stored=True),
		'company_id' : fields.many2one('res.company',string='Company',stored=False),
		'user_id' : fields.many2one('res.users',string='User',stored=False),
		'sequence_id' : fields.many2one('ir.sequence',string='Sequencia',stored=False),
		'amounttext': fields.function(_get_totalt,type='char',string='Total',stored=False),
		'doc_type':fields.selection([
			('check','Check'),
			('voucher','Voucher'),
			],'Default Type', ),	
		}

	def to_word(self,number, mi_moneda):
	    valor= number
	    number=int(number)
	    centavos=int((round(valor-number,2))*100)
	    UNIDADES = (
	    '',
	    'UN ',
	    'DOS ',
	    'TRES ',
	    'CUATRO ',
	    'CINCO ',
	    'SEIS ',
	    'SIETE ',
	    'OCHO ',
	    'NUEVE ',
	    'DIEZ ',
	    'ONCE ',
	    'DOCE ',
	    'TRECE ',
	    'CATORCE ',
	    'QUINCE ',
	    'DIECISEIS ',
	    'DIECISIETE ',
	    'DIECIOCHO ',
	    'DIECINUEVE ',
	    'VEINTE '
	)

	    DECENAS = (
	    'VENTI',
	    'TREINTA ',
	    'CUARENTA ',
	    'CINCUENTA ',
	    'SESENTA ',
	    'SETENTA ',
	    'OCHENTA ',
	    'NOVENTA ',
	    'CIEN '
	)

	    CENTENAS = (
	    'CIENTO ',
	    'DOSCIENTOS ',
	    'TRESCIENTOS ',
	    'CUATROCIENTOS ',
	    'QUINIENTOS ',
	    'SEISCIENTOS ',
	    'SETECIENTOS ',
	    'OCHOCIENTOS ',
	    'NOVECIENTOS '
	)
	    MONEDAS = (
		    {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
		    {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
		    {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
		    {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
		    {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
		    {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
		    {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
		)
	    if mi_moneda != None:
		try:
		    moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
		    if number < 2:
		        moneda = moneda['singular']
		    else:
		        moneda = moneda['plural']
		except:
		    return "Tipo de moneda inválida"
	    else:
		moneda = ""
	    """Converts a number into string representation"""
	    converted = ''

	    if not (0 < number < 999999999):
		return 'No es posible convertir el numero a letras'

	    number_str = str(number).zfill(9)
	    millones = number_str[:3]
	    miles = number_str[3:6]
	    cientos = number_str[6:]

	    if(millones):
		if(millones == '001'):
		    converted += 'UN MILLON '
		elif(int(millones) > 0):
		    converted += '%sMILLONES ' % self.convert_group(millones)

	    if(miles):
		if(miles == '001'):
		    converted += 'MIL '
		elif(int(miles) > 0):
		    converted += '%sMIL ' % self.convert_group(miles)

	    if(cientos):
		if(cientos == '001'):
		    converted += 'UN '
		elif(int(cientos) > 0):
		    converted += '%s ' % self.convert_group(cientos)
	    if(centavos)>0:
		converted+= "con %2i/100 "%centavos
	    converted += moneda

	    return converted.title()


	def convert_group(self,n):
	    UNIDADES = (
	    '',
	    'UN ',
	    'DOS ',
	    'TRES ',
	    'CUATRO ',
	    'CINCO ',
	    'SEIS ',
	    'SIETE ',
	    'OCHO ',
	    'NUEVE ',
	    'DIEZ ',
	    'ONCE ',
	    'DOCE ',
	    'TRECE ',
	    'CATORCE ',
	    'QUINCE ',
	    'DIECISEIS ',
	    'DIECISIETE ',
	    'DIECIOCHO ',
	    'DIECINUEVE ',
	    'VEINTE '
	)

	    DECENAS = (
	    'VENTI',
	    'TREINTA ',
	    'CUARENTA ',
	    'CINCUENTA ',
	    'SESENTA ',
	    'SETENTA ',
	    'OCHENTA ',
	    'NOVENTA ',
	    'CIEN '
	)

	    CENTENAS = (
	    'CIENTO ',
	    'DOSCIENTOS ',
	    'TRESCIENTOS ',
	    'CUATROCIENTOS ',
	    'QUINIENTOS ',
	    'SEISCIENTOS ',
	    'SETECIENTOS ',
	    'OCHOCIENTOS ',
	    'NOVECIENTOS '
	)
	    MONEDAS = (
		    {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
		    {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
		    {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
		    {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
		    {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
		    {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
		    {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
		)
	    """Turn each group of numbers into letters"""
	    output = ''

	    if(n == '100'):
		output = "CIEN "
	    elif(n[0] != '0'):
		output = CENTENAS[int(n[0]) - 1]

	    k = int(n[1:])
	    if(k <= 20):
		output += UNIDADES[k]
	    else:
		if((k > 30) & (n[2] != '0')):
		    output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
		else:
		    output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

	    return output

class retentions_lines(osv.osv):
	_name = 'retention.lines'
	
	_columns = {
		'account_id':fields.many2one('account.account','Account',required=True),
		'description': fields.char('Description',copy=False,required=True),
		'amount': fields.float(string='Amount',required=True),
		'voucher_id' : fields.many2one('account.voucher','Vid',required=False),
		'retention_id' : fields.many2one('retentions','Retentions',required=False),
		}

