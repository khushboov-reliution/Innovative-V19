# -*- coding: utf-8 -*-
{
    'name': 'Purchase Customization',
    'version': '19.0.2.2.0',
    'summary': 'add discount on po based on sale order',
    'description': '''''',
    'category': 'Innovative',
    'author': 'Reliution',
    'company': 'Reliution',
    'maintainer': 'Reliution',
    'depends': ['sale', 'purchase', 'product'],
    'data': [
        'security/ir.model.access.csv',
		'views/discount_slab_views.xml',
        'views/res_partner_view.xml',
        'views/purchase_order_view.xml',
		'report/purchase_order_custom_report.xml',
],
    'sequence': 1,
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
