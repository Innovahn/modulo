# -*- encoding: utf-8 -*-

import openerp.addons.decimal_precision as dp
from openerp import models, fields, api, exceptions, _
from openerp.osv import  osv
from datetime import datetime

class fund_requisition(models.Model):
	_name = 'funds.requisition'
	_description = 'Funds Requisition'
        
	
	def get_currency(self):
		return self.env.user.company_id.currency_id.id
			
	def _get_my_department(self):
		employees = self.env.user.employee_ids
        	return (employees[0].department_id if employees
                	else self.env['hr.department'])

	week_number=fields.Char(string="# Semana")
	date = fields.Date(string="Fecha",required=True, readonly=True, states={'draft': [('readonly', False)]})
	journal_id = fields.Many2one("account.journal", string="Journal")
	name = fields.Char(default=lambda self:self.env['ir.sequence'].get('funds'), readonly=True,
                              help="Id for each Fund Requisition", string="# Req. Fondos", states={'draft': [('readonly', False)]})
	reference = fields.Char(string="Proveedor", required=True,readonly=True,states={'draft': [('readonly', False)]})
	total = fields.Float(string="Monto Solicitado", required=True, digits_compute=dp.get_precision('Account'),readonly=True, states={'draft': [('readonly', False)]})
	department_id = fields.Many2one('hr.department', 'Departamento', default=_get_my_department, readonly=True,states={'draft': [('readonly', False)]})
	state = fields.Selection([('draft','Borrador'),('confirmed','Esperando Aprobación'),('reject','Rechazado'),('done','Aprobado')],string='Estado',default='draft')
        fund_currency=fields.Many2one("res.currency", "Moneda", readonly=True,required=True, states={'draft': [('readonly', False)]}, domain=[('active','=',True)], default=get_currency)

	description= fields.Text(string="Notas")
	_defaults = {
		'date' : datetime.now(),
		    } 

	@api.multi
	def action_draft(self):
		self.write({'state' : 'draft'})

	@api.multi
    	def action_reject(self):
		self.write({'state':'reject'})
        @api.multi
    	def action_confirmed(self):
		self.write({'state':'confirmed'})

	@api.multi
    	def action_approval(self):
		self.write({'state':'done'})
	
        @api.depends("name")
	@api.onchange("department_id")
	def onchange_department(self):
		 if self.department_id.name:
			secuencia=self.env['ir.sequence'].get('funds')
            		self.name= self.department_id.name +" " + str(secuencia)
		
	@api.onchange("date")
	def onchange_date(self):
		vdate= datetime.now()
        	vdate=datetime.strptime(self.date,"%Y-%m-%d")
        	self.week_number=str(vdate.isocalendar()[1])

	def unlink(self, cr, uid, ids, context=None):
		for f in self.browse(cr, uid, ids,context = context):
			if f.state == 'done':
				raise osv.except_osv(_('Error!'),_("This document is in Validated state, you can't delete it") )
			else:
				super(fund_requisition,self).unlink(cr, uid, ids, context =  context)
