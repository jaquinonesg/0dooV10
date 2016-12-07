#-*- coding:utf-8 -*-d
from openerp import models, fields, api, exceptions, _
from openerp.exceptions import Warning
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    #atualizat todos os clientes para (all) que nao estajam aprovisionados e termo de pagamento dif. de imediato
    def update_cron_warning_type(self, cr, uid, context=None):
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [('warning_type', '!=', False),'|', ('property_payment_term_id', '=', False),('property_payment_term_id.name', 'not ilike', 'imediato')], context=context)
        for partner_id in partner_obj.browse(cr, uid, partner_ids, context=context):
            cr.execute("update res_partner set warning_type='all' where id = "+str(partner_id.id))
        return True
 
    warning_type = fields.Selection([('none', 'Nenhum'),('blocked', 'Aprovisionado'), ('value', 'Valor'), ('date', 'Date'), ('all', 'Todos')], string='Aviso', required=True,  copy=False, default='all')
    credit_limit = fields.Float(string="Limite de Crédito", copy=False)
    credit_limit_days = fields.Integer(string="Limite de Dias em Crédito", copy=False, default='30')

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _get_payment_earliest_due_date(self,partner_id):
        date_maturity = False
	_logger.info("_get_payment_earliest_due_date")
        if partner_id:
            sql = " select min(date_maturity) from account_move_line aml inner join account_account aa on aa.id = aml.account_id inner join account_account_type aat on aat.id = aa.user_type_id where partner_id = %s and aat.type = 'receivable' and reconciled is False "%partner_id
            self.env.cr.execute(sql)
            date_maturity = self.env.cr.fetchone()
        if date_maturity:
            if date_maturity[0]:
                date_maturity = date_maturity[0]
                return date_maturity
        return False
    
    @api.model
    def create(self, vals):
        rec = super(sale_order_line, self).create(vals)
	_logger.info("create %s"%rec)
        if (not rec.order_id.payment_term_id) or (rec.order_id.payment_term_id and 'imediato' not in rec.order_id.payment_term_id.name):
            if rec.order_id and rec.order_id.partner_id.warning_type=='blocked':
                msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                    Pode passar a política de faturação para débito directo para poder faturar."'
                raise Warning(_(msg))
                return False
            if rec.order_id and rec.order_id.partner_id.warning_type!='none':
                if rec.order_id and rec.order_id.partner_id.warning_type in ('date','all'):
                    
                    d = timedelta(days=rec.order_id.partner_id.credit_limit_days)
                    data = False
		    if rec.order_id and rec.order_id.partner_id:
    		        data = self._get_payment_earliest_due_date(rec.order_id.partner_id.id)
                    #raise Warning(100)

                    #if not data: #self._get_payment_earliest_due_date(rec.order_id.partner_id.id)==False:
                    #    return True
                    # data = datetime.strptime(rec.order_id.partner_id.payment_earliest_due_date, '%Y-%m-%d')

                    if data:
                        data = datetime.strptime(data, '%Y-%m-%d')

                        if data + d < datetime.now():
                            msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                                Pode passar a política de faturação para débito directo para poder faturar."'
                            raise Warning(_(msg))
                            return False

                if rec.order_id and rec.order_id.partner_id.warning_type in ('value','all'):
                    domain = [('order_id.partner_id', '=', rec.order_id.partner_id.id),
                              ('invoice_status', '=', 'to invoice'),
                              ('order_id.state', 'not in', ['draft', 'cancel', 'sent'])]
                    order_lines = rec.env['sale.order.line'].search(domain)
                    none_invoiced_amount = sum([x.price_subtotal for x in order_lines])
                    # We sum from all the invoices that are in draft the total amount
                    domain = [
                        ('partner_id', '=', rec.order_id.partner_id.id), ('state', '=', 'draft')]
                    draft_invoices = self.env['account.invoice'].search(domain)
                    draft_invoices_amount = sum([x.amount_total for x in draft_invoices])

                    available_credit = rec.order_id.partner_id.credit_limit - \
                        rec.order_id.partner_id.credit - \
                        none_invoiced_amount - draft_invoices_amount
                    d = 0
		    #raise Warning(available_credit)
		    for x in rec.order_id.payment_term_id.line_ids:
                        d += x.days
                    if rec.order_id.amount_total > available_credit and d>0:
                        msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                                Pode passar a política de faturação para débito directo para poder faturar."'
                        raise Warning(_(msg))
                        return False
        return rec


    @api.multi
    def write(self, vals):
        if (not self.order_id.payment_term_id) or (self.order_id.payment_term_id and 'imediato' not in self.order_id.payment_term_id.name):
            if self.order_id and self.order_id.partner_id.warning_type=='blocked':
                msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                    Pode passar a política de faturação para débito directo para poder faturar."'
                raise Warning(_(msg))
                return False
            if self.order_id and self.order_id.partner_id.warning_type!='none':
                if self.order_id and self.order_id.partner_id.warning_type in ('date','all'):
                    d = timedelta(days=self.order_id.partner_id.credit_limit_days)
                    data = False
                    if self.order_id and self.order_id.partner_id:
                        data = self._get_payment_earliest_due_date(self.order_id.partner_id.id)
                    # if self.partner_id.payment_earliest_due_date==False:
                    #if self._get_payment_earliest_due_date(self.order_id.partner_id.id)==False:
                    #    return True
                    # data = datetime.strptime(self.order_id.partner_id.payment_earliest_due_date, '%Y-%m-%d')
                    #data = datetime.strptime(self._get_payment_earliest_due_date(self.order_id.partner_id.id), '%Y-%m-%d')
                    if data:
                        if data + d < datetime.now():
                            msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                                Pode passar a política de faturação para débito directo para poder faturar."'
                            raise Warning(_(msg))
                            return False
                if self.order_id and self.order_id.partner_id.warning_type in ('value','all'):
                    domain = [('order_id.partner_id', '=', self.order_id.partner_id.id),
                              ('invoice_status', '=', 'to invoice'),
                              ('order_id.state', 'not in', ['draft', 'cancel', 'sent'])]
                    order_lines = self.env['sale.order.line'].search(domain)
                    none_invoiced_amount = sum([x.price_subtotal for x in order_lines])
                    # We sum from all the invoices that are in draft the total amount
                    domain = [
                        ('partner_id', '=', self.order_id.partner_id.id), ('state', '=', 'draft')]
                    draft_invoices = self.env['account.invoice'].search(domain)
                    draft_invoices_amount = sum([x.amount_total for x in draft_invoices])

                    available_credit = self.order_id.partner_id.credit_limit - \
                        self.order_id.partner_id.credit - \
                        none_invoiced_amount - draft_invoices_amount
		    d = 0
                    for x in self.order_id.payment_term_id.line_ids:
                        d += int(x.days)
                    if self.order_id.amount_total > available_credit and d>0:
                        msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                                Pode passar a política de faturação para débito directo para poder faturar."'
                        raise Warning(_(msg))
                        return False
        return super(sale_order_line, self).write(vals)


class sale_order(models.Model):
    _inherit = "sale.order"

    @api.multi  
    def _get_payment_earliest_due_date(self,partner_id):
        date_maturity = False
        if partner_id:
            sql = " select min(date_maturity) from account_move_line aml inner join account_account aa on aa.id = aml.account_id "\
                    " inner join account_account_type aat on aat.id = aa.user_type_id where partner_id = %s and aat.type = 'receivable' "\
                    " and reconciled is False "%partner_id
            self.env.cr.execute(sql)
            date_maturity = self.env.cr.fetchone()
        if date_maturity:
            date_maturity = date_maturity[0]
        print '++++'
        print date_maturity
        print '++++'
        return date_maturity or False

    @api.one
    def action_wait(self):
        self.check_limit()
        return super(sale_order, self).action_wait()

    @api.one
    def action_confirm(self):
        self.check_limit()
        return super(sale_order, self).action_confirm()

    @api.one
    def check_limit(self):
        if self.payment_term_id and 'imediato' not in self.payment_term_id.name:
            if self.partner_id.warning_type!='none':
                if self.partner_id.warning_type in ('date','all'):
                    d = timedelta(days=self.partner_id.credit_limit_days)
                    print self._get_payment_earliest_due_date(self.partner_id.id)
                    if self._get_payment_earliest_due_date(self.partner_id.id) == False:
                    # if self.partner_id.payment_earliest_due_date==False:
                        return True
                    # data = self.partner_id.payment_earliest_due_date
                    data = self._get_payment_earliest_due_date(self.partner_id.id)
                    print data
                    _logger.info("data: %s"%data)
                    _logger.info("d: %s"%d)
                    _logger.info("tipo data: %s"%type(data))
                    _logger.info("tipo: %s"%type(d))
                    if data:
                        if datetime.strptime(data,'%Y-%m-%d') + d < datetime.now():
                            msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                                Pode passar a política de faturação para débito directo para poder faturar."'
                            raise Warning(_(msg))
                            return False
                if self.id and self.partner_id.warning_type in ('value','all'):
                    # We sum from all the sale orders that are aproved, the sale order
                    # lines that are not yet invoiced
                    domain = [('order_id.partner_id', '=', self.partner_id.id),
                              ('invoice_status', '=', 'to invoice'),
                              ('order_id.state', 'not in', ['draft', 'cancel', 'sent'])]
                    order_lines = self.env['sale.order.line'].search(domain)
                    none_invoiced_amount = sum([x.price_subtotal for x in order_lines])
                    # We sum from all the invoices that are in draft the total amount
                    domain = [
                        ('partner_id', '=', self.partner_id.id), ('state', '=', 'draft')]
                    draft_invoices = self.env['account.invoice'].search(domain)
                    draft_invoices_amount = sum([x.amount_total for x in draft_invoices])

                    available_credit = self.partner_id.credit_limit - \
                        self.partner_id.credit - \
                        none_invoiced_amount - draft_invoices_amount
                    if self.amount_total > available_credit:
                        msg = 'Não pode confirmar a ordem, porque o cliente não tem crédito suficiente. \
                                Pode passar a política de faturação para débito directo para poder faturar."'
                        raise Warning(_(msg))
                        return False
        return True
