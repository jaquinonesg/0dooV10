# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PosOrderExtended(models.Model):
    _inherit = "pos.order"
    @api.multi
    #def _create_account_move_line(self, session=None, move=None):
    def _create_account_move_line(self, session=None, move_id=None):
        move = False
        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        IrProperty = self.env['ir.property']
        ResPartner = self.env['res.partner']

        if session and not all(session.id == order.session_id.id for order in self):
            raise UserError(_('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False

        for order in self.filtered(lambda o: not o.account_move or order.state == 'paid'):
            current_company = order.sale_journal.company_id
            account_def = IrProperty.get(
                'property_account_receivable_id', 'res.partner')
            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
            if not move:
                # Create an entry for the sale
                journal_id = self.env['ir.config_parameter'].sudo().get_param(
                    'pos.closing.journal_id', default=order.sale_journal.id)
                move = self._create_account_move(
                    order.session_id.start_at, order.name, int(journal_id), order.company_id.id)
		move = self.env['account.move'].browse(move)
                _logger.info("Movimiento contable %s"%move)

            def insert_data(data_type, values):
                # if have_to_group_by:
	        _logger.info("INSER-DATA: PARTNER:%s"%partner_id)
	        _logger.info("INSER-DATA: MOVE:%s"%move)
                values.update({
                    'partner_id': partner_id,
                    'move_id': move.id,
                })

                if data_type == 'product':
                    key = ('product', values['partner_id'], (values['product_id'], tuple(values['tax_ids'][0][2]), values['name']), values['analytic_account_id'], values['debit'] > 0)
                elif data_type == 'tax':
                    key = ('tax', values['partner_id'], values['tax_line_id'], values['debit'] > 0)
                elif data_type == 'counter_part':
                    key = ('counter_part', values['partner_id'], values['account_id'], values['debit'] > 0)
                elif data_type == 'expense':
                    key = ('expense', values['partner_id'], (values['product_id'], values['name']), values['analytic_account_id'], values['debit'] > 0)
                elif data_type == 'stock_output':
                    key = ('stock_output', values['partner_id'], (values['product_id'], values['name']), values['analytic_account_id'], values['credit'] > 0)
                else:
                    return

                grouped_data.setdefault(key, [])

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        current_value = grouped_data[key][0]
                        current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                else:
                    grouped_data[key].append(values)

            # because of the weird way the pos order is written, we need to make sure there is at least one line,
            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
            # are set inside the for loop)
            # TOFIX: a deep refactoring of this method (and class!) is needed
            # in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line
            cur = order.pricelist_id.currency_id
            for line in order.lines:
                amount = line.price_subtotal

                # Search for the income account
                if line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))

                name = line.product_id.name
                if line.notice:
                    # add discount reason in move
                    name = name + ' (' + line.notice + ')'

                # Create a move for the line for the order line
                insert_data('product', {
                    'name': name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': income_account,
                    'analytic_account_id': self._prepare_analytic_account(line),
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'tax_ids': [(6, 0, line.tax_ids_after_fiscal_position.ids)],
                    'partner_id': partner_id
                })

                # Create the tax lines
                taxes = line.tax_ids_after_fiscal_position.filtered(lambda t: t.company_id.id == current_company.id)
                if not taxes:
                    continue
                for tax in taxes.compute_all(line.price_unit * (100.0 - line.discount) / 100.0, cur, line.qty)['taxes']:
                    insert_data('tax', {
                        'name': _('Tax') + ' ' + tax['name'],
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'account_id': tax['account_id'] or income_account,
                        'credit': ((tax['amount'] > 0) and tax['amount']) or 0.0,
                        'debit': ((tax['amount'] < 0) and -tax['amount']) or 0.0,
                        'tax_line_id': tax['id'],
                        'partner_id': partner_id
                    })
            # counterpart
            insert_data('counter_part', {
                'name': _("Trade Receivables"),  # order.name,
                'account_id': order_account,
                'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
                'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
                'partner_id': partner_id
            })
            amount_cost = line.qty * line.product_id.standard_price or 0.0
            if not line.product_id.product_tmpl_id._get_product_accounts()['expense']:
                raise UserError(_('Please define expense '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))
            # sale cost
            insert_data('expense', {
                'name': name,
                'quantity': line.qty,
                'product_id': line.product_id.id,
                'account_id': line.product_id.product_tmpl_id._get_product_accounts()['expense'].id,
                'analytic_account_id': self._prepare_analytic_account(line),
                'debit': ((amount_cost > 0) and amount_cost) or 0.0,
                'credit': ((amount_cost < 0) and -amount_cost) or 0.0,
                'partner_id': partner_id
            })
            if not line.product_id.product_tmpl_id._get_product_accounts()['stock_output']:
                raise UserError(_('Please define stock_output '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))

            # sale cost
            insert_data('stock_output', {
                'name': name,
                'quantity': line.qty,
                'product_id': line.product_id.id,
                'account_id': line.product_id.product_tmpl_id._get_product_accounts()['stock_output'].id,
                'analytic_account_id': self._prepare_analytic_account(line),
                'credit': ((amount_cost > 0) and amount_cost) or 0.0,
                'debit': ((amount_cost < 0) and -amount_cost) or 0.0,
                'partner_id': partner_id
            })

            order.write({'state': 'done', 'account_move': move.id})

        all_lines = []
        for group_key, group_data in grouped_data.iteritems():
            for value in group_data:
                all_lines.append((0, 0, value),)
        print all_lines
        if move:  # In case no order was changed
            move.sudo().write({'line_ids': all_lines})
            move.sudo().post()
        return True
