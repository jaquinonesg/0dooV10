# -*- coding: utf-8 -*-
{
    'name': "l10n_co_localization",

    'summary': """
        Colombian cities""",

    'description': """
        Colombian lozalization info
        =================================================================
        This module load colombian localization info (states and cities).
        Further, it load the code for each city and state generated by the
        DANE.
    """,

    'author': "Consultoría en Tecnoligía Informática CTI",
    #'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hidden',
    'version': '1.0',

    # any module necessary for this one to work correctlyi
    'depends': ['base'],

    # always loaded
    'data': [
        'data/res.country.state.csv',
        'data/res.country.state.city.csv',
        'security/ir.model.access.csv',
        'views/partner_city_view.xml',
        'views/bank_city_view.xml',
        'views/company_city_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': True,
}
