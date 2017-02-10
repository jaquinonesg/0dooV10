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

class account_treasury_report(models.Model):
    _name = "account.treasury.report"
    _description = "Treasury Analysis"
    _auto = False

    def _compute_balances(self, ids, field_names, arg=None, query='', query_params=()):
        cr = self._cr 
        uid = self.user_id.id
        ids = self.id
        context = self.env.context
        all_treasury_lines = self.search(cr, uid, [], context=context)
        all_companies = self.pool.get('res.company').search(cr, uid, [], context=context)
        current_sum = dict((company, 0.0) for company in all_companies)
        res = dict((id, dict((fn, 0.0) for fn in field_names)) for id in all_treasury_lines)
        for record in self.browse(cr, uid, all_treasury_lines, context=context):
            res[record.id]['starting_balance'] = current_sum[record.company_id.id] 
            current_sum[record.company_id.id] += record.balance
            res[record.id]['ending_balance'] = current_sum[record.company_id.id]
        return res    

    debit= fields.Float('Debit', readonly=True)
    credit= fields.Float('Credit', readonly=True)
    balance= fields.Float('Balance', readonly=True)
    date= fields.Date('Beginning of Period Date', readonly=True)
    date_maturity= fields.Date('Date Maturity', readonly=True)
    starting_balance= fields.Float(compute=_compute_balances, digits_compute=dp.get_precision('Account'), string='Starting Balance')
    ending_balance= fields.Float(compute=_compute_balances, digits_compute=dp.get_precision('Account'), string='Ending Balance')
    company_id= fields.Many2one('res.company', 'Company', readonly=True)

    _order = 'date asc'


    @api.model_cr
    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'account_treasury_report')
        cr.execute("""
            CREATE OR REPLACE VIEW account_treasury_report AS(
            SELECT row_number() over() as id,
                   l.Date,
                   l.Date_maturity,
                   SUM (l.debit) AS debit,
                   SUM (l.credit) AS credit,
                   SUM ( (l.debit - l.credit)) AS balance,
                   am.company_id
                FROM ((account_move_line l
                     LEFT JOIN account_account a ON ( (l.account_id = a.id)))
                     LEFT JOIN account_move am ON ( (am.id = l.move_id)))
                WHERE (((am.state)::text <> 'draft'::text)
                  AND ((a.internal_type)::text = 'liquidity'::text))
            GROUP BY l.Date, l.Date_maturity, am.company_id)
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
