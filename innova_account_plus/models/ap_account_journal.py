# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from datetime import datetime
from openerp.tools.translate import _

class irsecuence(osv.Model):
	_inherit = 'account.journal'
	def get_journal_exch(self, cr, uid, ids, context=None):
		journal_obj = self.pool.get('account.journal')
		diarios = journal_obj.browse(cr,uid,journal_obj.search(cr,uid,[],context=None),context=context)
		fl = False
		d_id= None
		for diario in diarios:
			if diario.sequence_ids:
				for sq in diario.sequence_ids:
					if sq.code == 'exch_diff':
						d_id = diario.id
						fl = True
		if fl:
			return d_id
		else:
			raise osv.except_osv(_('Error!'),_("There is not a journal with a sequence code 'exch_diff', please create one!"))

