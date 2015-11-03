# -*- encoding: utf-8 -*-
##############################################################################

{
    "name": "Financial",
    "version": "1.0",
    "depends": [
        "account",
        "purchase",
         "sale",	
	"hr",	
    ],
    "author": "Honduras Open Source",
    "category": "Financial",
    "description": """
        This module is the base for the financial module, Add a method for the Funds Requisitions
    """,
    'data': [
        "views/financial_menus.xml",
        "views/funds_requisition_view.xml",
	"views/funds_sequence.xml",
    ],
    'update_xml' : [
            'security/groups.xml',
            'security/ir.model.access.csv'
    ],
    'demo': [],
    'installable': True,
}
