# -*- coding: utf-8 -*-
{
    'name': "Apply chart template",

    'summary': """Apply chart template""",

    'description': """
        Apply chart template
    """,

    'author': "OxSoft SAS",
    'website': "http://www.oxsoft.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        #'chart_account_apply_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}
