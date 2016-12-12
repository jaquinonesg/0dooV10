# -*- coding: utf-8 -*-
{
    'name': "Módulo para extended los informes financieros de Odoo",

    'summary': """Extensión de Informes""",

    'description': """
        Este módulo permite extender los informes financieros
    """,

    'author': "BioxSolutions",
    'website': "http://www.bioxsolutions.com.ve",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'report/account_report_extended_view.xml',
        'report/account_report_financial_extended_view.xml',
        'views/account_report_general_ledger_extended_view.xml',
        'views/account_parent_extended_view.xml',
        'views/account_aged_trial_balance_extended_view.xml',
        #Data
        'data/account_parent_type_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}
