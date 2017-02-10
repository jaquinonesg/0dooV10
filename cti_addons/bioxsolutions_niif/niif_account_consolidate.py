# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError

class niif_account_consolidate(models.Model):
    _inherit = 'account.account'

    @api.one
    @api.depends('code','parent_id')
    def _get_puc(self):
        if self.code:
            if self.parent_id or len(self.code)>1:
                if self.code:
                    chart_account = self.env['account.account'].search([['code', '=', self.code[:1]]])
                    if chart_account:
                        self.chart_account = chart_account.id
                    elif not chart_account:
                        self.chart_account = self.env['account.account'].search([['code', '=', '0']])
                    elif not self.chart_account:
                        chart_account = self.env['account.account'].search([['code', '=', '0']])
                        raise UserError(_("You must define a Chart of Accounts"))

    child_consol_ids = fields.Many2many('account.account', 'account_account_consol_rel', 'child_id', 'parent_id', 'Consolidated Children',invisible=True)
    chart_account = fields.Many2one('account.account',string='Chart of Accounts', compute='_get_puc', store=True)
    parent_id = fields.Many2one('account.account',string='Parent')

class AccountAccountTypeExtended(models.Model):
    _inherit = "account.account.type"

    type = fields.Selection([
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
        ('view', _('View')),
        ('consolidation', _('Consolidation'))
    ], required=True, default='other',
        help="The 'Internal Type' is used for features available on "\
        "different types of accounts: liquidity type is for cash or bank accounts"\
        ", payable/receivable is for vendor/customer accounts.",oldname="type")

