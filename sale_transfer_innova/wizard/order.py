# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp.tools.translate import _
class stock_picking(osv.osv):
	_inherit ="stock.picking"
	def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
		a = super(stock_picking, self)._get_invoice_vals( cr, uid, key, inv_type, journal_id, move, context=None)
		print a
		a.update({'contrato_ids':move.picking_id.contrato_stock_ids.id,'date_invoice':move.picking_id.min_date})
		return a
class sale_order(osv.osv):
	_inherit = "sale.order"
	def transfer_stock_innova(self, cr, uid, ids, context=None):
		obj_wizard=self.pool.get('sale_transfer_innova.transfer')
		obj_wizard_line=self.pool.get('sale_transfer_innova.transfer_line')
		picking_obj = self.pool.get('stock.picking')
		move_obj = self.pool.get('stock.move')
		current_order=[0]
		wizard_id=obj_wizard.create(cr,uid,{},context=context)
		for current_order in self.browse(cr,uid,ids,context=context):
			data=self.prepare(current_order)
			obj_wizard.write(cr,uid,wizard_id,data,context=context)
			
			for line in current_order.order_line:
				picking_ids=[]
				for picking in current_order.picking_ids:
					picking_ids.append(picking.id)
				move_ids=move_obj.search(cr,uid,[('picking_id','in',picking_ids),('product_id','=',line.product_id.id)],context=context)
				qty=0
				for move in move_obj.browse(cr,uid,move_ids,context=context):
					qty+=move.product_uom_qty
				datal=self.prepare_line(line,wizard_id,qty)
				obj_wizard_line.create(cr,uid,datal,context=context)
				

		return {
			'type': 'ir.actions.act_window',
			'name': _('Orden de Salida de Plantas'),
			'res_model': 'sale_transfer_innova.transfer',
			'res_id': wizard_id,
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new',
		}

	def prepare(self,data):
		return {
			'picking_type_id': data.warehouse_id.out_type_id.id,
			'oe_origen': data.warehouse_id.out_type_id.default_location_src_id.id,
			'oe_destino':data.partner_id.property_stock_customer.id,
			'partner_id': data.partner_id.id,
			'order_id':data.id,
			'binvoce':False,
			'contract_id':data.contrato_ventas_ids.id,

			}
	def prepare_line(self,line,transfer_id,qty):
		nqty=line.product_uom_qty-qty
		if nqty<0:
			nqty=0
		return {
			'product_id': line.product_id.id,
			'qty':nqty,
			'transfer_id':transfer_id,
			'name':line.name
			}
			
	def action_button_confirm(self, cr, uid, ids, context=None):
		assert len(ids) == 1, 'This option should only be used for a single id at a time.'
		if context is None: context = {}
		res = False
		inv_id=self.action_done(cr,uid,ids,context=None)
		print inv_id
		print "##"*50
		return True
