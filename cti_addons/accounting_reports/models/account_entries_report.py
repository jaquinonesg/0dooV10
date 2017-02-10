# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp.addons.decimal_precision as dp

from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp import tools

class account_entries_report(models.Model):
    _name = "account.entries.report"
    _description = "Journal Items Analysis"
    _auto = False
    _rec_name = 'date'

    date= fields.Date('Effective Date', readonly=True)
    create_date= fields.Date('Date Created', readonly=True)
    date_maturity= fields.Date('Date Maturity', readonly=True)
    ref= fields.Char('Reference', readonly=True)
    nbr= fields.Integer('# of Items', readonly=True)
    debit= fields.Float('Debit', readonly=True)
    credit= fields.Float('Credit', readonly=True)
    balance= fields.Float('Balance', readonly=True)
    currency_id= fields.Many2one('res.currency', 'Currency', readonly=True)
    amount_currency= fields.Float('Amount Currency', digits_compute=dp.get_precision('Account'), readonly=True)
    account_id= fields.Many2one('account.account', 'Account', readonly=True)
    journal_id= fields.Many2one('account.journal', 'Journal', readonly=True)
    product_id= fields.Many2one('product.product', 'Product', readonly=True)
    product_uom_id= fields.Many2one('product.uom', 'Product Unit of Measure', readonly=True)
    move_state= fields.Selection([('draft','Unposted'), ('posted','Posted')], 'Status', readonly=True)
    partner_id= fields.Many2one('res.partner','Partner', readonly=True)
    analytic_account_id= fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    quantity= fields.Float('Products Quantity', digits=(16,2), readonly=True)
    user_type_id= fields.Many2one('account.account.type', 'Account Type', readonly=True)
    internal_type= fields.Selection([
            ('other', 'Regular'),
            ('receivable', 'Receivable'),
            ('payable', 'Payable'),
            ('liquidity', 'Liquidity'),
        ],'Internal type', readonly=True, help="This type is used to differentiate types with "\
        "special effects in Odoo.")
    company_id= fields.Many2one('res.company', 'Company', readonly=True)

    _order = 'date desc'

    @api.model_cr
    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'account_entries_report')
        cr.execute("""
            create or replace view account_entries_report as (
            select
                l.id as id,
                am.Date as date,
                l.Date_maturity as date_maturity,
                l.create_date as date_created,
                am.ref as ref,
                am.state as move_state,
                l.partner_id as partner_id,
                l.product_id as product_id,
                l.product_uom_id as product_uom_id,
                am.company_id as company_id,
                am.journal_id as journal_id,
                l.account_id as account_id,
                l.analytic_account_id as analytic_account_id,
                a.internal_type as internal_type,
                a.user_type_id as user_type_id,
                1 as nbr,
                l.quantity as quantity,
                l.currency_id as currency_id,
                l.amount_currency as amount_currency,
                l.debit as debit,
                l.credit as credit,
                coalesce(l.debit, 0.0) - coalesce(l.credit, 0.0) as balance
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                where am.state != 'draft'
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
