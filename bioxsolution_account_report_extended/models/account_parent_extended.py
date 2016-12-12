# -*- coding: utf-8 -*-

import time
from openerp import api, fields, models, _


class AccountParentExtended(models.Model):
    _inherit = 'account.account'
    
    parent_id = fields.Many2one('account.account', string='Parent account', domain="[('user_type_id.type','=','view')]")

class AccountAccountTypeExtended(models.Model):
    _inherit = "account.account.type"

    type = fields.Selection([
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
        ('view', _('View')),
    ], required=True, default='other',
        help="The 'Internal Type' is used for features available on "\
        "different types of accounts: liquidity type is for cash or bank accounts"\
        ", payable/receivable is for vendor/customer accounts.",oldname="type")

