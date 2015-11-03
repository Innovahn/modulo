from openerp.osv import osv
from datetime import datetime
class reporte_retentions(osv.AbstractModel):
	_name = 'report.ap.retentions_print'
	def _get_date(cr, uid):
		return datetime.now()

	def _getuser(cr, uid, ids, context=None):
		user_pool = self.pool.get(cr, uid, ids, context=context)
		user_obj =user_pool.browse(cr, uid, uid, context=context)
		return user_obj.name

	def render_html(self, cr, uid, ids, data=None, context=None):
		self.cr=cr
		self.uid=uid
		report_obj = self.pool['report']
		report = report_obj._get_report_from_name(cr, uid, 'innova_account_plus.retention_lines_print')
		docargs = {
			'doc_ids': ids,
			'doc_model': report.model,
			'docs': self.pool[report.model].browse(cr, uid, ids, context=context),
			'user': self._getuser(cr, uid, ids, context=context),
			}
		return report_obj.render(cr, uid, ids, 'innova_account_plus.retention_lines_print',docargs, context=context)

