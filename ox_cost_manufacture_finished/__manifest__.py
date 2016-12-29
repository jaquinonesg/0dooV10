# -*- coding: utf-8 -*-
{
    'name': "Cost Manufacture Product Finished",

    'summary': """Cost Manufacture Product Finished""",

    'description': """
        Cost Manufacture Product Finished
    """,

    'author': "OxSoft SAS",
    'website': "http://www.oxsoft.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'MRP',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mrp','mrp_byproduct','quality_control'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'cost_manufacture_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}
