# -*- coding: utf-8 -*-
{
    'name': "Product Label ",

    'summary': """
       inhert the product label to be printed in a label printer""",

    'description': """
        inherit the report of product variants in odoo
    """,

    'author': "Grupo Innova",
    'website': "http://www.innovahn.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product',],

    # always loaded
    'data': [
	'views/report_format_paper.xml',
	'views/product_report_inherit.xml',
    ],
    # only loaded in demonstration mode
   
}
