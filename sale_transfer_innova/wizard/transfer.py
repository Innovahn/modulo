from openerp.osv import osv,fields
from openerp.tools.translate import _
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
class transfer_Wizard(osv.TransientModel):
	_name = 'sale_transfer_innova.transfer'
	def validate(self, cr, uid, ids, context=None):
		picking_obj = self.pool.get('stock.picking')
		move_obj = self.pool.get('stock.move')
		order_obj = self.pool.get('sale.order')
		transfer_obj= self.pool.get('stock.transfer_details')
		transfer_item_obj = self.pool.get('stock.transfer_details_items')
		obj_wizard_line=self.pool.get('sale_transfer_innova.transfer_line')
		obj_onshiping=self.pool.get('stock.invoice.onshipping')
		tlines=context.get('lines',False)
		type_pick =context.get('picking_type_id',False)
		customer_dir=context.get('oe_destino',False)
		warehouse_dir=context.get('oe_origen',False)
		partner_id=context.get('partner_id',False)
		contract_id=context.get('contract_id',False)
		print "#"*5
		print contract_id
		binvoce=context.get('binvoce',False)
		dateorder=context.get('date',False)
		dateorder=datetime.strptime(dateorder, "%Y-%m-%d")+relativedelta(hours=6)
		order_id=context.get('order_id',False)
		journal_id=context.get('journal_id',False)
		order=order_obj.browse(cr,uid,order_id,context=context)
		proc_ids = []
            	vals = order_obj._prepare_procurement_group(cr, uid, order, context=context)
            	group_id=False
           	if not order.procurement_group_id:
                	group_id = self.pool.get("procurement.group").create(cr, uid, vals, context=context)
                	order.write({'procurement_group_id': group_id})
		inv_name=order.name
		group_id=order.procurement_group_id.id
		pick_id= picking_obj.create(cr,uid,{'min_date':dateorder,'partner_id':partner_id,'move_type':'direct','invoice_state':'2binvoiced','picking_type_id':type_pick,'priority':'1','contrato_stock_ids':contract_id,},context=context)
		dmove=[]
		for tline in tlines:
			line= obj_wizard_line.browse(cr,uid,tline[1],context=context)
			if line.qty>0:
				val={	'product_id':line.product_id.id,
					'product_uom':line.product_id.product_tmpl_id.uom_id.id,
					'product_uom_qty':line.qty,
					'name':line.name,
					'invoice_state':'2binvoiced',
					'date':dateorder,
					'date_expected':dateorder,
					'location_id':warehouse_dir,
					'location_dest_id':customer_dir,
					'origin':inv_name,
					'picking_id':pick_id,
					'group_id':group_id,
					
					}
				move_id=move_obj.create(cr,uid,val,context=context)
				dmove.append(move_id)
		if binvoce:
			context.update({'active_ids':[pick_id]})
			onshiping_id=obj_onshiping.create(cr,uid,{'journal_id':journal_id,'journal_type':'sale','date_invoice':dateorder,'contrato_ids':contract_id},context=context)
			return obj_onshiping.open_invoice(cr,uid,[onshiping_id],context=context)
		
		return {
			'type': 'ir.actions.act_window',
			'name': _('Detalle de Transferencia'),
			'res_model': 'stock.picking',
			'res_id': pick_id,
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'current',
		}
		

	_columns = {
		'picking_type_id': fields.many2one('stock.picking.type', 'Tipo', change_default=True, select=1),
		'oe_origen': fields.many2one('stock.location', 'Origen', change_default=True, select=1),
		'oe_destino':fields.many2one('stock.location', 'Destino', change_default=True, select=1,),
		'partner_id': fields.many2one('res.partner', 'Cliente', change_default=True, select=1),
		'order_id': fields.many2one('sale.order', 'Orden', change_default=True, select=1),
		'lines'	:fields.one2many('sale_transfer_innova.transfer_line','transfer_id',string='lineas'),
		'date':fields.date(string="Fecha"),
		'note':fields.text(string="Nota"),
		'binvoce':fields.boolean(string="Generar Factura"),
		'journal_id':fields.many2one('account.journal', 'Diario', domain=[('type','=','sale')],change_default=True, select=1),
		'contract_id':fields.many2one('contratos.contractsale', 'No. Contract', select=1,),
		}
	_defaults = {
	'date' : lambda *a: time.strftime("%Y-%m-%d 06:00:00"),
		}
class transfer_Wizard_line(osv.TransientModel):
	_name = 'sale_transfer_innova.transfer_line'
	_columns = {
		'product_id': fields.many2one('product.product', 'Producto', change_default=True, select=1),
		'qty':fields.float('Cantidad'),

		'transfer_id':fields.many2one('sale_transfer_innova.transfer', 'Transferencia', change_default=True, select=1,),
		'name':fields.char(string="Name")
		}
