# -*- coding: utf-8 -*-
{
    'name': "Módulo para la gestión de NIIF",

    'summary': """Módulo para la gestión de NIIF""",

    'description': """
        Módulo para la gestión de NIIF
    """,

    'author': "BioxSolutions",
    'website': "http://www.bioxsolutions.com.ve",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_budget','account_accountant'],

    # always loaded
    'data': [
        'niif_account_consolidate_view.xml',
        'data/account_type_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}
