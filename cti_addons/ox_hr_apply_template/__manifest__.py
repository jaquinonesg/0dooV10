# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'HR Apply template',
    'version' : '1.1',
    'summary': 'HR Apply template',
    'sequence': 30,
    'description': """
    'author': 'OxSoft SAS',
    """,
    'category': 'Payroll',
    'website': 'https://www.oxsoft.com.co',
    'images' : [],
    'depends' : ['hr_payroll','3rp_hr'],
    'data': [
        'views/hr_apply_template_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
