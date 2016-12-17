# -*- coding: utf-8 -*-
{
    'name': "accounting_reports",

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
    'depends': ['account','account_accountant', 'analytic'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_entries_report_view.xml',
        'views/account_treasury_report_view.xml',
        'views/account_analytic_entries_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}