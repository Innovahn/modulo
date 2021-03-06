# -*- coding: utf-8 -*-


from openerp import models, fields, exceptions, api, _
import openerp.addons.decimal_precision as dp
from datetime import datetime


class PurchaseCostDistribution(models.Model):
    _name = "purchase.cost.distribution"
    _description = "Purchase landed costs distribution"
    _order = 'name desc'
    
    #Suma de total de orden de compra + suma de gastos 
    @api.one
    @api.depends('total_expense', 'total_purchase')
    def _compute_amount_total(self):
        self.amount_total = self.total_purchase + self.total_expense

    #Costo de Lineas que suma el precio unitario de todos los productos por las cantidades
    @api.one
    @api.depends('cost_lines', 'cost_lines.total_amount')
    def _compute_total_purchase(self):
        self.total_purchase = sum([x.total_amount for x in self.cost_lines])
 
    #Suma de todos los precios unitarios to do aun no se para que se usa esta funcion
    @api.one
    @api.depends('cost_lines', 'cost_lines.product_price_unit')
    def _compute_total_price_unit(self):
        self.total_price_unit = sum([x.product_price_unit for x in
                                     self.cost_lines])
    #Suma La cantidades totales de inventario
    @api.one
    @api.depends('cost_lines', 'cost_lines.product_qty')
    def _compute_total_uom_qty(self):
        self.total_uom_qty = sum([x.product_qty for x in self.cost_lines])
    #Suma de pesos
    @api.one
    @api.depends('cost_lines', 'cost_lines.total_weight')
    def _compute_total_weight(self):
        self.total_weight = sum([x.total_weight for x in self.cost_lines])

    @api.one
    @api.depends('cost_lines', 'cost_lines.total_weight_net')
    def _compute_total_weight_net(self):
        self.total_weight_net = sum([x.total_weight_net for x in
                                     self.cost_lines])
     #Suma de totales de volumenes
    @api.one
    @api.depends('cost_lines', 'cost_lines.total_volume')
    def _compute_total_volume(self):
        self.total_volume = sum([x.total_volume for x in self.cost_lines])
    #Suma de los gastos desde la segunda page revisar la mondeda que viene
    @api.one
    @api.depends('expense_lines', 'expense_lines.expense_amount')
    def _compute_total_expense(self):
	for x in self.expense_lines:
		currency  = None
		if x.invoice_line:
			if x.invoice_line.invoice_id.currency_id.id == self.currency_id.id:
				self.total_expense += x.expense_amount
			else:
				currency = self.currency_id.with_context(date=datetime.now())
				invoice_currency = x.invoice_line.invoice_id.currency_id.with_context(date=datetime.now())
				
				rate = None
				if invoice_currency.rate:
					rate = 	 currency.rate / invoice_currency.rate
				
				self.total_expense += rate*(x.expense_amount)
		else:
			self.total_expense += x.expense_amount
	#self.total_expense = sum([x.expense_amount for x in self.expense_lines])
        

    def _expense_lines_default(self):
        expenses = self.env['purchase.expense.type'].search(
            [('default_expense', '=', True)])
        return [{'type': x} for x in expenses]

    name = fields.Char(string='Distribution number', required=True,
                       select=True, default='/')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=(lambda self: self.env['res.company']._company_default_get(
            'purchase.cost.distribution')))
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Currency',
        related="company_id.currency_id")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('calculated', 'Calculated'),
         ('done', 'Done'),
         ('error', 'Error'),
         ('cancel', 'Cancel')], string='Status', readonly=True,
        default='draft')
    cost_update_type = fields.Selection(
        [('direct', 'Direct Update')], string='Cost Update Type',
        default='direct', required=True)
    date = fields.Date(
        string='Date', required=True, readonly=True, select=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today)
    total_uom_qty = fields.Float(
        compute=_compute_total_uom_qty, readonly=True,
        digits_compute=dp.get_precision('Product UoS'),
        string='Total quantity')
    total_weight = fields.Float(
        compute=_compute_total_weight, string='Total gross weight',
        readonly=True,
        digits_compute=dp.get_precision('Stock Weight'))
    total_weight_net = fields.Float(
        compute=_compute_total_weight_net,
        digits_compute=dp.get_precision('Stock Weight'),
        string='Total net weight', readonly=True)
    total_volume = fields.Float(
        compute=_compute_total_volume, string='Total volume', readonly=True)
    total_purchase = fields.Float(
        compute=_compute_total_purchase,
        digits_compute=dp.get_precision('Account'), string='Total purchase')
    total_price_unit = fields.Float(
        compute=_compute_total_price_unit, string='Total price unit',
        digits_compute=dp.get_precision('Product Price'))
    amount_total = fields.Float(
        compute=_compute_amount_total,
        digits_compute=dp.get_precision('Account'), string='Total')
    total_expense = fields.Float(
        compute=_compute_total_expense,
        digits_compute=dp.get_precision('Account'), string='Total expenses')
    note = fields.Text(string='Documentation for this order')
    cost_lines = fields.One2many(
        comodel_name='purchase.cost.distribution.line', ondelete="cascade",
        inverse_name='distribution', string='Distribution lines')
    expense_lines = fields.One2many(
        comodel_name='purchase.cost.distribution.expense', ondelete="cascade",
        inverse_name='distribution', string='Expenses',
        default=_expense_lines_default)

    @api.multi
    def unlink(self):
        for c in self:
            if c.state not in ('draft', 'calculated'):
                raise exceptions.Warning(
                    _("You can't delete a confirmed cost distribution"))
        return super(PurchaseCostDistribution, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'purchase.cost.distribution')
        return super(PurchaseCostDistribution, self).create(vals)

    @api.multi
    def action_calculate(self):
        for distribution in self:
            # Check expense lines for amount 0
            if any([not x.expense_amount for x in distribution.expense_lines]):
                raise exceptions.Warning(
                    _('Please enter an amount for all the expenses'))
            # Check if exist lines in distribution
            if not distribution.cost_lines:
                raise exceptions.Warning(
                    _('There is no picking lines in the distribution'))
            # Calculating expense line
            for line in distribution.cost_lines:
                line.expense_lines.unlink()
		expenses_final = 0.0
		expense_id = None
                for expense in distribution.expense_lines:
                    if (expense.affected_lines and
                            line.id not in expense.affected_lines.ids):
                        continue
                    if expense.type.calculation_method == 'amount':
                        multiplier = line.total_amount
                        if expense.affected_lines:
                            divisor = sum([x.total_amount for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_purchase
                    elif expense.type.calculation_method == 'price':
                        multiplier = line.product_price_unit
                        if expense.affected_lines:
                            divisor = sum([x.product_price_unit for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_price_unit
                    elif expense.type.calculation_method == 'qty':
                        multiplier = line.product_qty
                        if expense.affected_lines:
                            divisor = sum([x.product_qty for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_uom_qty
                    elif expense.type.calculation_method == 'weight':
                        multiplier = line.total_weight
                        if expense.affected_lines:
                            divisor = sum([x.total_weight for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_weight
                    elif expense.type.calculation_method == 'weight_net':
                        multiplier = line.total_weight_net
                        if expense.affected_lines:
                            divisor = sum([x.total_weight_net for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_weight_net
                    elif expense.type.calculation_method == 'volume':
                        multiplier = line.total_volume
                        if expense.affected_lines:
                            divisor = sum([x.total_volume for x in
                                           expense.affected_lines])
                        else:
                            divisor = distribution.total_volume
                    elif expense.type.calculation_method == 'equal':
                        multiplier = 1
                        divisor = (len(expense.affected_lines) or
                                   len(distribution.cost_lines))
                    else:
                        raise exceptions.Warning(
                            _('No valid distribution type.'))
                    expense_amount = (expense.expense_amount * multiplier /
                                      divisor)

		    if expense.invoice_line:
			if expense.invoice_line.invoice_id.currency_id.id == self.currency_id.id:
		            expenses_final += expense_amount						
			else:
		            currency = self.currency_id.with_context(date=datetime.now())
		            invoice_currency = expense.invoice_line.invoice_id.currency_id.with_context(date=datetime.now())
		            rate = None
		            if invoice_currency.rate != 0:
			        rate = currency.rate / invoice_currency.rate
			        expenses_final += rate*(expense_amount)
			    else:
			        raise exceptions.Warning(_('Please add a currency rate for the invoces in the lines'))	

		    else:
		        expenses_final += expense_amount	
		    # TODO Alejandro Rodriguez Quitar estas linea de codigos una vez validad esta operacion	
		    #if expense.invoice_line.invoice_id.currency_id.id == self.currency_id.id:
		    #	expenses_final += expense_amount 
		    #else:
		    #    currency = self.currency_id.with_context(date=datetime.now())
		    #    invoice_currency = expense.invoice_line.invoice_id.currency_id.with_context(date=datetime.now())
		    #    rate = None
		    #    if invoice_currency.rate != 0:
			#    rate = currency.rate / invoice_currency.rate
			 #   expenses_final += rate*(expense_amount)
			#else:
			 #   raise exceptions.Warning(_('Please add a currency rate for the invoces in the lines'))	
			    
		    expense_id = expense.id
                expense_line = {
		        'distribution_expense': expense_id,
		        'expense_amount': expenses_final,
		        'cost_ratio': expenses_final / line.product_qty,
                }
	       	
                line.expense_lines = [(0, 0, expense_line)]
            distribution.state = 'calculated'
        return True

    @api.multi
    def action_done(self):
        for distribution in self:
            for line in distribution.cost_lines:
                if distribution.cost_update_type == 'direct':
                    line.product_id.standard_price = line.standard_price_new
            distribution.state = 'done'
        return True

    @api.multi
    def action_draft(self):
        for distribution in self:
            distribution.state = 'draft'
        return True

    @api.multi
    def action_cancel(self):
        for distribution in self:
            for line in distribution.cost_lines:
                if distribution.currency_id.compare_amounts(
                        line.product_id.standard_price,
                        line.standard_price_new) != 0:
                    raise exceptions.Warning(
                        _('Cost update cannot be undone because there has '
                          'been a later update. Restore correct price and try '
                          'again.'))
                line.product_id.standard_price = line.standard_price_old
            distribution.state = 'draft'
        return True


class PurchaseCostDistributionLine(models.Model):

    @api.one
    @api.depends('product_price_unit', 'product_qty')
    def _compute_total_amount(self):
        self.total_amount = self.product_price_unit * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight(self):
        self.total_weight = self.product_weight * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight_net(self):
        self.total_weight_net = self.product_weight_net * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_volume(self):
        self.total_volume = self.product_volume * self.product_qty

    @api.one
    @api.depends('expense_lines', 'expense_lines.cost_ratio')
    def _compute_cost_ratio(self):
        self.cost_ratio = sum([x.cost_ratio for x in self.expense_lines])

    #SUMATORIA DE LOS GASTOS   
    @api.one
    @api.depends('expense_lines', 'expense_lines.expense_amount')
    def _compute_expense_amount(self):
	for x in self.expense_lines:
		self.expense_amount=+ x.expense_amount
		
        #self.expense_amount = sum([x.expense_amount for x in self.expense_lines])

    @api.one
    @api.depends('standard_price_old', 'cost_ratio')
    def _compute_standard_price_new(self):
        self.standard_price_new = self.standard_price_old + self.cost_ratio

    _name = "purchase.cost.distribution.line"
    _description = "Purchase cost distribution Line"

    @api.one
    @api.depends('move_id', 'move_id.picking_id', 'move_id.product_id',
                 'move_id.product_qty')
    def _compute_display_name(self):
        self.name = '%s / %s / %s' % (
            self.move_id.picking_id.name, self.move_id.product_id.display_name,
            self.move_id.product_qty)

    @api.one
    @api.depends('move_id', 'move_id.product_id')
    def _get_product_id(self):
        # Cannot be done via related field due to strange bug in update chain
        self.product_id = self.move_id.product_id.id

    @api.one
    @api.depends('move_id', 'move_id.product_qty')
    def _get_product_qty(self):
        # Cannot be done via related field due to strange bug in update chain
        self.product_qty = self.move_id.product_qty

    name = fields.Char(
        string='Name', compute='_compute_display_name')
    distribution = fields.Many2one(
        comodel_name='purchase.cost.distribution', string='Cost distribution',
        ondelete='cascade')
    move_id = fields.Many2one(
        comodel_name='stock.move', string='Picking line', ondelete="restrict")
    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Purchase order line',
        related='move_id.purchase_line_id')
    purchase_id = fields.Many2one(
        comodel_name='purchase.order', string='Purchase order', readonly=True,
        related='purchase_line_id.order_id')
    partner = fields.Many2one(
        comodel_name='res.partner', string='Supplier', readonly=True,
        related='purchase_id.partner_id')
    picking_id = fields.Many2one(
        'stock.picking', string='Picking', related='move_id.picking_id')
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', store=True,
        compute='_get_product_id')
    product_qty = fields.Float(
        string='Quantity', compute='_get_product_qty', store=True)
    product_uom = fields.Many2one(
        comodel_name='product.uom', string='Unit of measure',
        related='move_id.product_uom')
    product_uos_qty = fields.Float(
        string='Quantity (UoS)', related='move_id.product_uos_qty')
    product_uos = fields.Many2one(
        comodel_name='product.uom', string='Product UoS',
        related='move_id.product_uos')
    product_price_unit = fields.Float(
        string='Unit price', related='move_id.price_unit')
    expense_lines = fields.One2many(
        comodel_name='purchase.cost.distribution.line.expense',
        inverse_name='distribution_line', string='Expenses distribution lines',
        ondelete='cascade')
    expense_lines_good = fields.One2many(
        comodel_name='purchase.cost.distribution.expense',
        inverse_name='distribution', string='Expenses distribution lines',
        ondelete='cascade')	
    product_volume = fields.Float(
        string='Volume', help="The volume in m3.",
        related='product_id.product_tmpl_id.volume')
    product_weight = fields.Float(
        string='Gross weight', related='product_id.product_tmpl_id.weight',
        help="The gross weight in Kg.")
    product_weight_net = fields.Float(
        string='Net weight', related='product_id.product_tmpl_id.weight_net',
        help="The net weight in Kg.")
    standard_price_old = fields.Float(
        string='Previous cost',
        digits_compute=dp.get_precision('Product Price'))
    expense_amount = fields.Float(
        string='Cost amount', digits_compute=dp.get_precision('Account'),
        compute='_compute_expense_amount')
    cost_ratio = fields.Float(
        string='Unit cost', digits_compute=dp.get_precision('Account'),
        compute='_compute_cost_ratio')
    standard_price_new = fields.Float(
        string='New cost', digits_compute=dp.get_precision('Product Price'),
        compute='_compute_standard_price_new')
    total_amount = fields.Float(
        compute=_compute_total_amount, string='Amount line',
        digits_compute=dp.get_precision('Account'))
    total_weight = fields.Float(
        compute=_compute_total_weight, string="Line weight", store=True,
        digits_compute=dp.get_precision('Stock Weight'),
        help="The line gross weight in Kg.")
    total_weight_net = fields.Float(
        compute=_compute_total_weight_net, string='Line net weight',
        digits_compute=dp.get_precision('Stock Weight'), store=True,
        help="The line net weight in Kg.")
    total_volume = fields.Float(
        compute=_compute_total_volume, string='Line volume', store=True,
        help="The line volume in m3.")


class PurchaseCostDistributionLineExpense(models.Model):
    _name = "purchase.cost.distribution.line.expense"
    _description = "Purchase cost distribution line expense"

    distribution_line = fields.Many2one(
        comodel_name='purchase.cost.distribution.line',
        string='Cost distribution line', ondelete="cascade")
    distribution_expense = fields.Many2one(
        comodel_name='purchase.cost.distribution.expense',
        string='Distribution expense', ondelete="cascade")
    type = fields.Many2one(
        'purchase.expense.type', string='Expense type',
        related='distribution_expense.type')
    expense_amount = fields.Float(
        string='Expense amount', default=0.0,
        digits_compute=dp.get_precision('Account'))
    cost_ratio = fields.Float(
        'Unit cost', default=0.0,
        digits_compute=dp.get_precision('Account'))


class PurchaseCostDistributionExpense(models.Model):
    _name = "purchase.cost.distribution.expense"
    _description = "Purchase cost distribution expense"

    @api.one
    @api.depends('distribution', 'distribution.cost_lines')
    def _get_imported_lines(self):
        self.imported_lines = self.env['purchase.cost.distribution.line']
        self.imported_lines |= self.distribution.cost_lines
    @api.one
    @api.depends('invoice_line', 'distribution.currency_id')
    def _get_currency_invoice_line(self):
        if self.invoice_line:
            self.currency_id = self.invoice_line.invoice_id.currency_id	
	else:
	    self.currency_id = self.distribution.currency_id

    distribution = fields.Many2one(
        comodel_name='purchase.cost.distribution', string='Cost distribution',
        select=True, ondelete="cascade", required=True)
    ref = fields.Char(string="Reference",required=True)
    type = fields.Many2one(
        comodel_name='purchase.expense.type', string='Expense type',
        select=True, ondelete="restrict", required=True)
    calculation_method = fields.Selection(
        string='Calculation method', related='type.calculation_method',
        readonly=True)
    imported_lines = fields.Many2many(
        comodel_name='purchase.cost.distribution.line',
        string='Imported lines', compute='_get_imported_lines')
    affected_lines = fields.Many2many(
        comodel_name='purchase.cost.distribution.line', column1="expense_id",
        relation="distribution_expense_aff_rel", column2="line_id",
        string='Affected lines',
        help="Put here specific lines that this expense is going to be "
             "distributed across. Leave it blank to use all imported lines.",
        domain="[('id', 'in', imported_lines[0][2])]")
    expense_amount = fields.Float(
        string='Expense amount', digits_compute=dp.get_precision('Account'),
        required=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency', string='Moneda', compute='_get_currency_invoice_line')
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line', string="Supplier invoice line",
        domain="[('invoice_id.type', '=', 'in_invoice'),"
               "('invoice_id.state', 'in', ('open', 'paid'))]")
