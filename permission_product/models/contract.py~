# -*- encoding: utf-8 -*-
from openerp import models, fields, api 
class Contractsale(models.Model):
    _name="contratos.contractsale"

    name=fields.Char(default=lambda self:self.env['ir.sequence'].get('contrato'),readonly=True, 
                              help="# de Contrato", string="No. Contrato",states={'draft': [('readonly', False)]})
    partner_id=fields.Many2one('res.partner','Customer', required=True, readonly=True,states={'draft': [('readonly', False)]},ondelete="set null", domain=[('customer', '=', True)],
                               help="Customer you are making the agreement with",index=True)
    country=fields.Char('Country',readonly=True,states={'draft': [('readonly', False)]})
    project= fields.Many2one("crossovered.budget", "Project name", readonly=True,states={'draft': [('readonly', False)]},ondelete="set null",help='Name that helps to identify the project', 
                             index=True)
    state=fields.Selection(
        [('draft', 'Borrador'),
         ('cancel', 'Cancelado'),  ('done', 'Confirmado')], string='Estado', readonly=True,
        default='draft')
    active=fields.Boolean(string="Active contract", default=True)
    amount_plants=fields.Char("Cantidad de plantas", readonly=True,states={'draft': [('readonly', False)]},help="Canitdad de plantas del contrato")
    add_plants=fields.Float("Plantas adicionales (%)", readonly=True,states={'draft': [('readonly', False)]},help="Canitdad de plantas adicionales para el contrato")
    start_date=fields.Date("Start Date",readonly=True,states={'draft': [('readonly', False)]},help="Please write a start date")
    end_date=fields.Date("End Date",readonly=True,states={'draft': [('readonly', False)]},help="Please write a end date")
    description=fields.Text()
    ventas_ids=fields.One2many("sale.order","contrato_ventas_ids","Contratos")
    account_invoice_ids=fields.One2many('account.invoice',"contrato_ids","Facturas")
    product_id=fields.Many2one("product.template","Variedad de cultivo",readonly=True,states={'draft': [('readonly', False)]},ondelete="set null", domain=[('sale_ok','=',True)],index=True)
    monto_total=fields.Float("Monto del contrato", readonly=True,states={'draft': [('readonly', False)]},help="Monto total del contrato")
    currency_contract=fields.Many2one("res.currency", "Moneda",readonly=True,states={'draft': [('readonly', False)]},domain=[('active','=',True)], default="USD")
    entrega_move=fields.One2many('stock.picking','contrato_stock_ids','Entrega de Plantas')
    anticipo_cliente=fields.One2many('account.voucher','contrato_sale','Anticipo de Cliente')
    #plantas_entregadas=fields.Float(string='Plantas Entregadas')
    
    #@api.one
    #@api.depends("entrega_move", "entrega_move.quantity_total")
    #def get_plant_qty(self):
        #for picking in self.eentrega_move:
		#if self.entrega_move.state=='done':
			#print "*"*23
			#self.plantas_entregadas += self.entrega_move.quantity_total
			#print self.plantas_entregadas
			#print "*"*223

    @api.onchange("partner_id")
    def _onchangecountry(self):
        self.country=self.partner_id.country_id.name

    @api.multi
    def action_draft(self):
	self.write({'state':'draft'})
     
    @api.multi
    def action_done(self):
	self.write({'state':'done'})

    @api.multi
    def action_cancel(self):
	self.write({'state':'cancel'})   
   
  
    

    
