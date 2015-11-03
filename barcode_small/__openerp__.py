# -*- coding: utf-8 -*-
{
    'name': 'Print Barcode Small',
    'author': 'Alejandro Rodriguez',
    'depends': ['base', 'decimal_precision', 'mail', 'report'],
    'demo': [
        'product_demo.xml',
        'product_image_demo.xml',
    ],
    'description': """
This is the base module for managing products and pricelists in OpenERP.
    """,
    'data': [
        'product_report.xml',
        'views/report_pricelist.xml',
    ],
    'installable': True,
    'auto_install': False,
}

