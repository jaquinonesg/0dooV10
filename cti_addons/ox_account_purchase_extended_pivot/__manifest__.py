# -*- coding: utf-8 -*-
{
    'name': "Purchase line (pivot, graph)",

    'summary': """Purchase line (pivot, graph)""",

    'description': """
        Este módulo agrega la opción de analizar las lineas de los pedidos de compras mediante pivot y gráficos
    """,

    'author': "OxSoft SAS",
    'website': "http://www.oxsoft.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'purchase_extended_pivot_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo.xml',
    ],
}
