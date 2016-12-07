# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) David Arnold (devCO).
# Author        David Arnold (devCO), dar@devco.co
# Co-Authors    Juan Pablo Aries (devCO), jpa@devco.co
#               Hector Ivan Valencia Muñoz (TIX SAS)
#               Nhomar Hernandez (Vauxoo)
#               Humberto Ochoa (Vauxoo)

{
    'name': 'Colombian - Accounting',
    'version': '0.1',
    'category': 'Localization',
    'description': 'Colombian Accounting and Tax Preconfiguration',
    'author': 'Carlos Martinez Camelo',
    'depends': [
        'account',
        'base_vat',
    ],
    'data': [
        'data/l10n_co_chart_data.xml',
        'data/account.account.template.csv',
#        'data/account_chart_template_data.xml',
        'data/account.tax.template.csv',
#        'data/account_tax_group_data.xml',
#        'data/account_chart_template_data.yml',
    ],
}
