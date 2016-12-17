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

from openerp import models, fields, api, tools, _

class budget_line_report(models.Model):
    _name = 'budget.line.report'
    _description = 'View for budget line report'
    _auto = False

    account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True, readonly=True)
    general_account_id = fields.Many2one('account.account', string='Financial Account', readonly=True) 
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    date = fields.Date('Date', required=True, index=True, readonly=True)
    amount = fields.Monetary(currency_field='company_currency_id', readonly=True)
    unit_amount = unit_amount = fields.Float('Quantity', default=0.0, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    company_currency_id = fields.Many2one('res.currency', readonly=True, related='company_id.currency_id', 
                          help='Utility field to express amount currency')


    @api.model_cr
    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'budget_line_report')
        cr.execute("""
        	CREATE OR REPLACE VIEW budget_line_report AS
            SELECT a.company_id, a.account_id, a.general_account_id, 
                   a.partner_id, a.product_id, a.date, SUM(a.amount) amount, 
                   SUM(a.unit_amount) unit_amount
              FROM account_analytic_line a LEFT JOIN
                   crossovered_budget_lines c ON (a.partner_id = c.partner_id AND a.product_id = c.product_id)
              GROUP BY a.company_id, a.account_id, a.general_account_id, a.date, a.partner_id, a.product_id
        """)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: