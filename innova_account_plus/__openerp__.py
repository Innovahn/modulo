# -*- coding: utf-8 -*-
{	
	'name' : 'Innova Account Plus',
	'author': 'Grupo Innova',
	'category': 'Generic Modules/Accounting',
	'summary': 'This module allows calculate exchange difference',
	'description': """Account Plus by Innova HN""",

	'data':[	
		'wizard/exchange_diff.xml',
		'wizard/retention_lines_assing.xml',
		'views/exchange_diference.xml',
		'views/ap_account_voucher_cp.xml',
		'views/ap_account_voucher_sp.xml',
		'views/account_account_view.xml',
		'views/retention_lines.xml',
		'views/retentions.xml',
		'data/sequence_and_codes.xml',
		'reports/retention_paper_format.xml',		
		'reports/retentions_print.xml',
		'views/retention_reports.xml',
		
	],
	'update_xml' : [
			'security/groups.xml',
			'security/ir.model.access.csv'
	],
	'depends': ['base','account_accountant','account_voucher'],
    	'installable': True,
}
