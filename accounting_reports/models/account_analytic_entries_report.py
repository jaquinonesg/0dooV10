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

from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp import tools

class analytic_entries_report(models.Model):
    _name = "analytic.entries.report"
    _description = "Analytic Entries Statistics"
    _auto = False
    
    date= fields.Date('Date', readonly=True)
    user_id= fields.Many2one('res.users', 'User',readonly=True)
    name= fields.Char('Description', size=64, readonly=True)
    partner_id= fields.Many2one('res.partner', 'Partner')
    company_id= fields.Many2one('res.company', 'Company', required=True)
    currency_id= fields.Many2one('res.currency', 'Currency', required=True)
    account_id= fields.Many2one('account.analytic.account', 'Account', required=False)
    general_account_id= fields.Many2one('account.account', 'General Account', required=True)
    move_id= fields.Many2one('account.move.line', 'Move', required=True)
    product_id= fields.Many2one('product.product', 'Product', required=True)
    product_uom_id= fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    amount= fields.Float('Amount', readonly=True)
    unit_amount= fields.Integer('Unit Amount', readonly=True)
    nbr= fields.Integer('# Entries', readonly=True)
    

    @api.model_cr
    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'analytic_entries_report')
        cr.execute("""
            CREATE OR REPLACE VIEW analytic_entries_report AS (
                SELECT min(a.id) AS id,
                       count(DISTINCT a.id) AS nbr,
                       a.date,
                       a.user_id,
                       a.name,
                       analytic.partner_id,
                       a.company_id,
                       a.currency_id,
                       a.account_id,
                       a.general_account_id,
                       a.move_id,
                       a.product_id,
                       a.product_uom_id,
                       sum(a.amount) AS amount,
                       sum(a.unit_amount) AS unit_amount
                  FROM account_analytic_line a,
                       account_analytic_account analytic
                  WHERE (analytic.id = a.account_id)
                  GROUP BY a.date, a.user_id, a.name, analytic.partner_id, a.company_id, a.currency_id, a.account_id, a.general_account_id, a.move_id, a.product_id, a.product_uom_id
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: