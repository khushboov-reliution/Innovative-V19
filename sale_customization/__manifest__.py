# -*- coding: utf-8 -*-
{
    'name': 'Sale Customization',
    'version': '19.0.4.2.0',
    'summary': 'Add expiration terms, sales product last price, customer-based pricelist, product demand quantity,',
    'description': '''''',
    'category': 'Innovative',
    'author': 'Reliution',
    'company': 'Reliution',
    'maintainer': 'Reliution',
    'depends': ['base', 'mail','sale_management','ieppl_product_customization','stock','sale','delivery','account'],

    'data': [
        'security/ir.model.access.csv',
        'report/ir_actions_report_templates.xml',
        'report/sale_order_custom.xml',
        'views/sale_order_views.xml',
        'views/sale_details.xml',
        'views/stock_move_line_views.xml',
        'views/stock_picking_views.xml',
		'views/res_company.xml',
],
    'sequence': 1,
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
