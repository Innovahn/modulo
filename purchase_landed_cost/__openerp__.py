# -*- coding: utf-8 -*-



{
    'name': 'Purchase landed costs - Honduras Option',
    'version': '1.0',
    'author': 'Editado por Alejandro Rodriguez',
    'category': 'Purchase Management',
    'summary': 'Purchase cost distribution',
    'depends': [
        'stock',
        'purchase',
    ],
    'data': [
        'wizard/picking_import_wizard_view.xml',
        'wizard/import_invoice_line_wizard_view.xml',
        'views/purchase_cost_distribution_view.xml',
        'views/purchase_expense_type_view.xml',
	'views/stock_picking_view.xml',
        'data/purchase_cost_distribution_sequence.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'images': [
        '/static/description/images/purchase_order_expense_main.png',
        '/static/description/images/purchase_order_expense_line.png',
        '/static/description/images/expenses_types.png',
    ],
}
