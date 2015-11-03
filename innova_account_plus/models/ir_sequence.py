# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from datetime import datetime
from openerp.tools.translate import _

class irsecuence(osv.Model):
	_inherit = 'ir.sequence'

	def journal_number(self,cr,uid,ids,journalid,doc_type,context=None):
		if not journalid==False and doc_type !=False:
			context = dict(context or {})
			force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id#id of the company of the user
			seq_model = self.pool.get('ir.sequence')
			name = "/"
			journal_obj = self.pool.get('account.journal')
			diario = journal_obj.browse(cr,uid,journal_obj.search(cr,uid,[('id','=',journalid)],context=None),context=context)
			seq_id=None
			fl=False
			if diario.sequence_id:
				seq_id = diario.sequence_id.id
			else:
				raise osv.except_osv(_('Configuration Error !'),_('Please activate the sequence of selected journal !'))
			context.update({'no_update' : True})
			name = seq_model.next_by_id(cr, uid, int(seq_id),context=context)
			return  name
			
		else:
			return None


	def _next(self, cr, uid, ids, context=None):
		if not ids:
        		return False
        	if context is None:
         		context = {}
       		force_company = context.get('force_company')
        	if not force_company:
          		force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        	sequences = self.read(cr, uid, ids, ['name','company_id','implementation','number_next','prefix','suffix','padding'])
        	preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
        	seq = preferred_sequences[0] if preferred_sequences else sequences[0]
       		if seq['implementation'] == 'standard':
			if context.get('no_update'):
				raise osv.except_osv(_("Error"), _("Please configurate this journal sequence implementation as 'No gap'!"))
           		cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
          		seq['number_next'] = cr.fetchone()
       		else:
			cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
			if not context.get('no_update'):
				cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
            		self.invalidate_cache(cr, uid, ['number_next'], [seq['id']], context=context)
        	d = self._interpolation_dict()
        	try:
                	interpolated_prefix = self._interpolate(seq['prefix'], d)
            		interpolated_suffix = self._interpolate(seq['suffix'], d)
       		except ValueError:
            		raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
       		return interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix
	_columns = {
		'journal_id':fields.many2one('account.journal','sequence_ids')
		    }
