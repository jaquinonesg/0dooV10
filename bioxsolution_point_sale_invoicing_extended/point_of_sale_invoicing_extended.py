# -*- coding: utf-8 -*-

import psycopg2
import logging
from openerp import tools, models, SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)

class pos_order(osv.osv):
    _inherit = "pos.order"

    def create_from_ui(self, cr, uid, orders, context=None):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        existing_order_ids = self.search(cr, uid, [('pos_reference', 'in', submitted_references)], context=context)
        existing_orders = self.read(cr, uid, existing_order_ids, ['pos_reference'], context=context)
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]

        order_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']

            self._match_payment_to_invoice(cr, uid, order, context=context)

            order_id = self._process_order(cr, uid, order, context=context)
            order_ids.append(order_id)

            try:
                self.signal_workflow(cr, uid, [order_id], 'paid')
            except psycopg2.OperationalError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
            pos_order = self.browse(cr,uid,order_id,context)
            self.action_invoice(cr, uid, [order_id], context)
            order_obj = self.browse(cr, uid, order_id, context)
            self.pool['account.invoice'].signal_workflow(cr, SUPERUSER_ID, [order_obj.invoice_id.id], 'invoice_open')
        return order_ids