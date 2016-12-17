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
from datetime import date, datetime
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT

# ---------------------------------------------------------
# Utils
# ---------------------------------------------------------
def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

def strToDatetime(strdate):
    return datetime.strptime(strdate, DEFAULT_SERVER_DATE_FORMAT)


class crossovered_budget_lines(models.Model):
    _inherit = 'crossovered.budget.lines'

    def _prac_amt(self):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
        res = {}
        result = 0.0
        if context is None: 
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            acc_ids = [x.id for x in line.general_budget_id.account_ids]
            if not acc_ids:
                raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
            date_to = context.get('wizard_date_to') or line.date_to
            date_from = context.get('wizard_date_from') or line.date_from
            if line.analytic_account_id.id:
            	sql_params = {
            	    "account_id": line.analytic_account_id.id,
            	    "date_from": date_from, 
            	    "date_to": date_to,
            	    "general_account_id": acc_ids,
            	    "partner_id": line.partner_id.id,
            	    "product_id": line.product_id.id,
            	}
            	sql = ("SELECT SUM(amount) "
            	      "FROM  budget_line_report "
            	      "WHERE account_id = %(account_id)s "
            	      "AND (date BETWEEN to_date('%(date_from)s','yyyy-mm-dd') AND to_date('%(date_to)s','yyyy-mm-dd')) "
            	      "AND general_account_id = ANY(array%(general_account_id)s) ")
            	sql += "AND " + ("partner_id = %(partner_id)s " if line.partner_id else "partner_id IS NULL ")
            	sql += "AND " + ("product_id = %(product_id)s " if line.product_id else "product_id IS NULL ")
            	
                cr.execute(sql % sql_params)
                result = cr.fetchone()[0]
            if result is None:
                result = 0.00
            res[line.id] = result
        return res

    def _prac_qty_amt(self):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context

        res = {}
        result = 0.0
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            acc_ids = [x.id for x in line.general_budget_id.account_ids]
            if not acc_ids:
                raise UserError(_("The Budget '%s' has no accounts!") % ustr(line.general_budget_id.name))
            date_to = context.get('wizard_date_to') or line.date_to
            date_from = context.get('wizard_date_from') or line.date_from
            if line.analytic_account_id.id:
            	sql_params = {
            	    "account_id": line.analytic_account_id.id,
            	    "date_from": date_from, 
            	    "date_to": date_to,
            	    "general_account_id": acc_ids,
            	    "partner_id": line.partner_id.id,
            	    "product_id": line.product_id.id,
            	}
            	sql = ("SELECT SUM(unit_amount) "
            	      "FROM  budget_line_report "
            	      "WHERE account_id = %(account_id)s "
            	      "AND (date BETWEEN to_date('%(date_from)s','yyyy-mm-dd') AND to_date('%(date_to)s','yyyy-mm-dd')) "
            	      "AND general_account_id = ANY(array%(general_account_id)s) ")
            	sql += "AND " + ("partner_id = %(partner_id)s " if line.partner_id else "partner_id IS NULL ")
            	sql += "AND " + ("product_id = %(product_id)s " if line.product_id else "product_id IS NULL ")
            	
            	print sql % sql_params

                cr.execute(sql % sql_params)
                result = cr.fetchone()[0]
            if result is None:
                result = 0.00
            res[line.id] = result
        return res
    
    def _prac_qty(self):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
    	res={}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = self._prac_qty_amt(cr, uid, [line.id], context=context)[line.id]
        return res

    def _perc_qty(self):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context

    	res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.theoritical_quantity <> 0.00:
                res[line.id] = float((line.practical_quantity or 0.0) / line.theoritical_quantity) * 100
            else:
                res[line.id] = 0.00
        return res
    
    def _theo_qty_amt(self):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context

    	if context is None:
            context = {}

        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            today = datetime.now()
            # Used for the report
            if context.get('wizard_date_from') and context.get('wizard_date_to'):
                date_from = strToDatetime(context.get('wizard_date_from'))
                date_to = strToDatetime(context.get('wizard_date_to'))
                if date_from < strToDatetime(line.date_from):
                    date_from = strToDatetime(line.date_from)
                elif date_from > strToDatetime(line.date_to):
                    date_from = False

                if date_to > strToDatetime(line.date_to):
                    date_to = strToDatetime(line.date_to)
                elif date_to < strToDatetime(line.date_from):
                    date_to = False

                theo_amt = 0.00
                if date_from and date_to:
                    line_timedelta = strToDatetime(line.date_to) - strToDatetime(line.date_from)
                    elapsed_timedelta = date_to - date_from
                    if elapsed_timedelta.days > 0:
                        theo_qty = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_quantity
            else:
                if line.paid_date:
                    if strToDate(line.date_to) <= strToDate(line.paid_date):
                        theo_qty = 0.00
                    else:
                        theo_qty = line.planned_quantity
                else:

                    line_timedelta = strToDatetime(line.date_to) - strToDatetime(line.date_from)
                    elapsed_timedelta = today - (strToDatetime(line.date_from))

                    if elapsed_timedelta.days < 0:
                        # If the budget line has not started yet, theoretical amount should be zero
                        theo_qty = 0.00
                    elif line_timedelta.days > 0 and today < strToDatetime(line.date_to):
                        # If today is between the budget line date_from and date_to
                        # from pudb import set_trace; set_trace()
                        theo_qty = (elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_quantity
                    else:
                        theo_qty = line.planned_quantity

            res[line.id] = theo_qty
        return res

    def _theo_qty(self):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context

    	res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = self._theo_qty_amt(cr, uid, [line.id], context=context)[line.id]
        return res

    product_id= fields.Many2one('product.product', string='Product')
    partner_id= fields.Many2one('res.partner', string='Partner')
    planned_quantity= fields.Float('Planned Quantity', required=True, digits=0)
    practical_quantity= fields.Float(compute="_prac_qty", string='Practical Quantity')
    theoritical_quantity= fields.Float(compute="_theo_qty", string='Theoretical Quantity')
    percentage_quantity= fields.Float(compute="_perc_qty", string='Achievement Quantity')