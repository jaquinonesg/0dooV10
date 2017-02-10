# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'MRP Invoice',
    'version' : '1.1',
    'summary': 'MRP Invoice',
    'sequence': 30,
    'description': """
    """,
    'category': 'Accounting',
    'website': 'https://www.oxsoft.com.co',
    'images' : [],
    'depends' : ['account_accountant','quality_control'],
    'data': [
        'views/mrp_invoice_view.xml',
        'data/concepts_quality_data.xml',
        'reports/report_mrp_invoice.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
