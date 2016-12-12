# -*- coding: utf-8 -*-
{
    'name': "Extension selling point for billing",

    'summary': """The extender module allows POS , para Perform automatic billing.""",

    'description': """
    """,

    'author': "BioxSolutions",
    'website': "http://www.bioxsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'POS',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': ['views/point_of_sale.xml'],
    # only loaded in demonstration mode
    'demo': [
    ],
}
