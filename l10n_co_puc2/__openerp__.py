# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) Consultoría en Tecnología Informática (CTI Ltda.).
# Author        Consultoría en Tecnología Informática (CTI Ltda.).

{
    'name': 'Colombian - Accounting',
    'version': '9.0.1',
    'category': 'Localization/Account Charts',
    'description': 'Colombian Accounting and Tax Preconfiguration',
    'author': 'Consultoría en Tecnología Informática (CTI Ltda.)',
    'depends': [
        'account',
    ],
    'data': [
        'data/account.account.tag.csv',
        'data/account_chart_template_before.xml',
        'data/account.account.template.csv',
        'data/account_chart_template.xml',
#        'data/account.tax.template.csv',
        'data/account_tax_group.xml',
        'data/account_chart_template.yml',
    ],
    'demo': [],
    'installable': True,
}
