# -*- coding: utf-8 -*-
{
    'name': "account_budget_additional_info",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_budget'],

    # always loaded
    'data': [
        'views/crossovered_budget_view.xml',
        'views/crossovered_budget_lines_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}