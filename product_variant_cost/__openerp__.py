# -*- encoding: utf-8 -*-
##############################################################################

{
    "name": "Product Variant Cost",
    "depends": [
        "product",
        "stock_account"
    ],
    "author": "Editado",
    "category": "Product",
    "summary": "",
    "data": [
        "views/product_view.xml",
        "views/stock_quant_view.xml"
    ],
    "installable": True,
    "post_init_hook": "load_cost_price_on_variant",
}
