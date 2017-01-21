# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import date, datetime, timedelta
import time
import pytz

_logger = logging.getLogger(__name__)

class MRPProductInvoice(models.Model):
    _inherit = 'product.product'

    mrp_invoice = fields.Boolean(string='MRP Invoice?',default=False)

class MRPInvoice(models.Model):
    _inherit = 'account.invoice'

    base = fields.Float(string='Base',default=0.0)
    mim_id = fields.One2many('monthly.inventory.movements','invoice_id',string='Monthly Inventory Movements')
    ci_id = fields.One2many('compositional.information','invoice_id',string='Compositional Information')
    dr_id = fields.One2many('daily.reception','invoice_id',string='Daily Reception')
    cq_id = fields.Many2many('concepts.quality','invoice_quality_rel','invoice_id','cq_id','Concepts quality')
    amount_quality = fields.Float(string='Amount quality')

    @api.model
    def create(self, vals):
        self = super(MRPInvoice, self).create(vals)
        self.mrp_invoice(vals)
        return self

    def mrp_invoice(self,vals=None):
        mim,dr,ci = {},{},{}
        date_invoice = None
        if not self.date_invoice and vals:
            date_invoice = vals.get('date_invoice')
        if not date_invoice:
            date_invoice = datetime.now()
            vals['date_invoice'] = date_invoice

        for line in self.invoice_line_ids:
            if line.product_id.mrp_invoice:
                #monthly.inventory.movements
                move = self.env['stock.move'].search([('product_id','=',line.product_id.id),('state','=','done')])
                for mov in move:
                    if mov.picking_id.picking_type_id.code == 'incoming':
                        #account move for month
                        if not self.date_invoice:
                            self.date_invoice = datetime.now()
                        if self.date_invoice[0:4] == mov.date_expected[0:4]:
                            if 'm'+str(int(mov.date_expected[5:7])) not in mim.keys():
                                mim['m'+str(int(mov.date_expected[5:7]))] = mov.product_uom_qty
                            else:
                                mim['m'+str(int(mov.date_expected[5:7]))] += mov.product_uom_qty
                #daily.reception
                date_invoice_ini = str(datetime.strptime(str(date_invoice)[0:10],'%Y-%m-%d') - timedelta(days=15))[0:10]
                move = self.env['stock.move'].search([('product_id','=',line.product_id.id),('state','=','done'),('date_expected','>=',date_invoice_ini),('date_expected','<=',str(date_invoice)[0:10])])
                for mov in move:
                    if mov.picking_id.picking_type_id.code == 'incoming':
                        #dialy reception
                        date_mov = mov.date_expected[0:10]
                        #adjust time zone self.env.user
                        tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
                        start = pytz.utc.localize(datetime.strptime(mov.date_expected,'%Y-%m-%d %H:%M:%S')).astimezone(tz)
                        tz_date = start.strftime("%Y-%m-%d")
                        diff = (datetime.strptime(str(date_invoice)[0:10],'%Y-%m-%d') - datetime.strptime(str(tz_date)[0:10],'%Y-%m-%d')).days

                        if diff in range(0,16):
                            if 'd'+str(int(15 - diff)) not in dr.keys():
                                dr['d'+str(int(15 - diff))] = mov.product_uom_qty
                            else:
                                dr['d'+str(int(15 - diff))] += mov.product_uom_qty

                tlts = 0
                for ddrl in dr:
                    _logger.info(ddrl)
                    tlts += float(dr[ddrl])
                if not dr.get('value'):
                    dr['value'] = line.product_id.standard_price
                if not dr.get('total_value'):
                    dr['total_value'] = tlts
                if not dr.get('total'):
                    dr['total'] = tlts * line.product_id.standard_price
                #compositional.information
                date_purchase = str(datetime.strptime(str(date_invoice)[0:10],'%Y-%m-%d') - timedelta(days=45))[0:10]
                orders = self.env['purchase.order'].search([('partner_id','=',self.partner_id.id),('date_order','>=',date_purchase),('date_order','<=',str(date_invoice)[0:10])])
                for order in orders:
                    diff = (datetime.strptime(str(date_invoice)[0:10],'%Y-%m-%d') - datetime.strptime(str(order.date_order)[0:10],'%Y-%m-%d')).days
                    for qc in self.env['qc.inspection'].search([('state','=','success')]):
                        if qc.object_id == order:
                            for lines in qc.inspection_lines:
                                _logger.info('diff:'+str(diff))
                                _logger.info(order.name)
                                _logger.info(lines.test_line.name)
                                if lines.test_line.name not in ci.keys():
                                    ci[lines.test_line.name] = {'product_id':line.product_id.id,'qc_question_id':lines.test_line.id,'qna1':0,'qna2':0,'qna3':0,'avg':0}
                                if diff >0 and diff<=15:
                                    ci[lines.test_line.name]['qna3'] += float(lines.quantitative_value)
                                elif diff > 15 and diff <=30:
                                    ci[lines.test_line.name]['qna2'] += float(lines.quantitative_value)
                                else:
                                    ci[lines.test_line.name]['qna1'] += float(lines.quantitative_value)
                                ci[lines.test_line.name]['avg'] = (ci[lines.test_line.name]['qna1'] + ci[lines.test_line.name]['qna2'] + ci[lines.test_line.name]['qna3'])/3

        self.mim_id = None
        self.dr_id = None
        self.ci_id = None
        _logger.info('--------')
        _logger.info(mim)
        _logger.info(dr)
        _logger.info(ci)
        _logger.info('--------')
        self.mim_id = [(0, 0, mim)]
        self.dr_id = [(0, 0, dr)]
        for x in ci:
            self.ci_id = [(0, 0, ci[x])]
        #create default concepts quality
        self.cq_id = None
        cq = self.env['concepts.quality'].search([])
        self.cq_id = [(6, 0, [x.id for x in cq])]
        #calculate amount quality
        self.amount_quality = 0
        for quality in self.cq_id:
            self.amount_quality += quality.amount

class MonthlyInventoryMovements(models.Model):
    _name = "monthly.inventory.movements"

    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    m1 = fields.Float(string='January',default=0.0)
    m2 = fields.Float(string='February',default=0.0)
    m3 = fields.Float(string='March',default=0.0)
    m4 = fields.Float(string='April',default=0.0)
    m5 = fields.Float(string='May',default=0.0)
    m6 = fields.Float(string='June',default=0.0)
    m7 = fields.Float(string='July',default=0.0)
    m8 = fields.Float(string='August',default=0.0)
    m9 = fields.Float(string='September',default=0.0)
    m10 = fields.Float(string='October',default=0.0)
    m11 = fields.Float(string='November',default=0.0)
    m12 = fields.Float(string='December',default=0.0)

class CompositionalInformation(models.Model):
    _name = "compositional.information"

    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    product_id = fields.Many2one('product.product',string='Product')
    qc_question_id = fields.Many2one('qc.test.question',string='QC Test Question')
    qna1 = fields.Float(string='Fortnight 1', default=0.0)
    qna2 = fields.Float(string='Fortnight 2', default=0.0)
    qna3 = fields.Float(string='Fortnight 3', default=0.0)
    avg = fields.Float(string='Average', default=0.0)

class ConceptsQuality(models.Model):
    _name = "concepts.quality"

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    # sign = fields.Selection([('+','+'),('-','-')],string='Sign')
    amount = fields.Float(string='Amount')

class DailyReception(models.Model):
    _name = "daily.reception"

    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    value = fields.Float(string='Value', default=0.0)
    d1 = fields.Float(string='Day 1', default=0.0)
    d2 = fields.Float(string='Day 2', default=0.0)
    d3 = fields.Float(string='Day 3', default=0.0)
    d4 = fields.Float(string='Day 4', default=0.0)
    d5 = fields.Float(string='Day 5', default=0.0)
    d6 = fields.Float(string='Day 6', default=0.0)
    d7 = fields.Float(string='Day 7', default=0.0)
    d8 = fields.Float(string='Day 8', default=0.0)
    d9 = fields.Float(string='Day 9', default=0.0)
    d10 = fields.Float(string='Day 10', default=0.0)
    d11 = fields.Float(string='Day 11', default=0.0)
    d12 = fields.Float(string='Day 12', default=0.0)
    d13 = fields.Float(string='Day 13', default=0.0)
    d14 = fields.Float(string='Day 14', default=0.0)
    d15 = fields.Float(string='Day 15', default=0.0)
    total_value = fields.Float(string='Total value', default=0.0)
    total = fields.Float(string='Total', default=0.0)
