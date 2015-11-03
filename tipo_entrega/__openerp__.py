# -*- coding: utf-8 -*-
{
"name":"Tipo de entrega",
"author": "Alejandro Rodriguez, Grupo Innova",
"description": "Tipo de entrega de plantas",
"category":"Sale",
"depends":["base",
           "sale"],
 "data": [
        "views/sale_enttrega_view.xml",
        ],
'update_xml' : [
            'security/groups.xml',
            'security/ir.model.access.csv'
    ],
    "auto_install": False,
    "installable": True,
}
