# -*- coding: utf-8 -*-
{
    'name': "Reports Generator",

    'summary': """Reports module para generate dynamic, and to export XLSX and PDF. : In addition to email them.""",

    'description': """
    Reports module para generate dynamic, and to export XLSX and PDF. : In addition to email them.
    """,

    'author': "BioxSolutions",
    'website': "http://www.bioxsolutions.com.ve",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Dashboard',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail','base'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/reports_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}
