# -*- coding: utf-8 -*-
{
    'name': "Informes para Impuestos",

    'summary': """Informes configurables para declaración de impuestos""",

    'description': """
        Este modulo permite configurar informes por categorías de impuestos y cuentas contables
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
        # 'security/ir.model.access.csv',
        'account_tax_report_view.xml',
        'report/account_tax_report_pdf.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}
