# -*- coding: utf-8 -*-
{	
	'name' : 'Sales Forecast',
	'author': 'Pedro Cabrera, Grupo Innova',
	'category': 'Generic Modules/Accounting',
	'summary': 'This module allows you to manage all about Sales forecast',
	'description': """Sales Forecast""",

	'data':[
		'views/sales_forecast.xml',
		'wizards/calculate_forecast.xml',
	],
	'update_xml' : [
			#'security/groups.xml',
			#'security/ir.model.access.csv'
	],
	'depends': ['base','hr','sale','financial'],
    	'installable': True,
}
