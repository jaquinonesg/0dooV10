# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import date, datetime, timedelta
from odoo.tools.safe_eval import safe_eval
import time
import pytz


_logger = logging.getLogger(__name__)

class MRPInvoice(models.Model):
    _inherit = 'account.invoice'

    base = fields.Float(string='Base',default=0.0)
    mim_id = fields.One2many('monthly.inventory.movements','invoice_id',string='Monthly Inventory Movements')
    ci_id = fields.One2many('compositional.information','invoice_id',string='Compositional Information')
    dr_id = fields.One2many('daily.reception','invoice_id',string='Daily Reception')
    cq_id = fields.Many2many('concepts.quality','invoice_quality_rel','invoice_id','cq_id','Concepts quality')
    amount_quality = fields.Float(string='Amount quality')
    type_test = fields.Selection([(1,'Protein & Fat'),(2,'Total solids')], string='type of test')
    hygienic_quality = fields.Selection([(1,'0 - 25,000',),(2,'25,001 - 50,000'),(3,'50,001 - 100,000'),(4,'100,001 - 150,000'),(5,'150,001 - 175,000'),(6,'175,001 - 200,000'),(7,'200,001 - 300,000'),(8,'300,001 - 400,000'),(9,'400,001 - 500,000'),(10,'500,001 - 600,000'),(11,'Mayores a 600.000')], string='Hygienic of quality')
    temperature = fields.Selection([(1,'Cool'),(2,'Without cool')], string='Temperature')
    sanitary_quality = fields.Selection([(1,'Hato libre de una enfermedad'),(2,'Hato libre de dos enfermedades'),(3,'Uncertified')], string='Sanitary Quality')
    certificate = fields.Selection([(1,'With BPG Certification'),(2,'Without BPG Certification')], string='Certificate')
    distance = fields.Selection([(1,'0 - 25'),(2,'26 - 50'),(3,'51 - 75'),(4,'76 - 100'),(5,'101 - 125'),(6,'126 - 150'),(7,'151 - 175'),(8,'176 - 200'),(9,'201 - 225'),(10,'226 - 250'),(11,'251 - 275'),(12,'276 - 300'),(13,'301 - 325'),(14,'326 - 350'),(15,'351 - 375'),(16,'376 - 400')], string="Distance")
    transport = fields.Selection([(1,'TRUCK TRACT'),(2,'LARGE TANK TRUCK'),(3,'LARGE TRUCK CANTINAS'),(4,'TRUCK SMALL TANK'),(5,'TRUCK SMALL CANTINAS')], string="Transport")

    def calculate(self):
        self.amount_quality = 0
        for concepts in self.cq_id:
            localdict = {}
            localdict['result'] = 0
            localdict['invoice'] = self
            safe_eval(concepts.code_python, localdict, mode='exec', nocopy=True)
            concepts.amount = localdict.get('result',0)
            self.amount_quality += concepts.amount

    @api.model
    def create(self, vals):
        self = super(MRPInvoice, self).create(vals)
        self.mrp_invoice(vals)
        return self

    def mrp_invoice(self,vals=None):
        mim,dr,ci,drt = {},{},{},{}
        wilfredo = 0
        date_invoice = None
        if not self.date_invoice and vals:
            date_invoice = vals.get('date_invoice')
        if not date_invoice:
            date_invoice = datetime.now()
            vals['date_invoice'] = date_invoice
        product = []
        for line in self.invoice_line_ids:
            if line.product_id.id not in product:
                product.append(line.product_id.id)

        #monthly.inventory.movements
        move = self.env['stock.move'].search([('product_id','in',product),('state','=','done')])
        for mov in move:
            if mov.picking_id.picking_type_id.code == 'incoming':
                #account move for month
                if not self.date_invoice:
                    self.date_invoice = datetime.now()
                if self.date_invoice[0:4] == mov.date_expected[0:4]:
                    if 'm'+str(int(mov.date_expected[5:7])) not in mim.keys():
                        mim['m'+str(int(mov.date_expected[5:7]))] = mov.product_uom_qty
                        mim['c'+str(int(mov.date_expected[5:7]))] = 1
                    else:
                        mim['m'+str(int(mov.date_expected[5:7]))] += mov.product_uom_qty
                        mim['c'+str(int(mov.date_expected[5:7]))] += 1
        #generar promedios
        mim['accumulated'] = 0.0
        for x in range(1, 13):
            mim['m'+str(x)] = mim.get('m'+str(x), 0) / (mim.get('c'+str(x),1))
            mim['accumulated'] += mim['m'+str(x)]

        origin = self.origin.split(', ')
        purchase = self.env['purchase.order'].search([('name','in',origin)])
        _logger.info('--------------------')
        arr = []
        for po in purchase:
            for line in po.order_line:
                if 'd'+str(int(line.date_planned[8:10])) not in drt.keys():
                    drt['d'+str(int(line.date_planned[8:10]))] = line.product_qty
                else:
                    drt['d'+str(int(line.date_planned[8:10]))] += line.product_qty
            
        for x in sorted(drt,reverse=True):
            for y in sorted(range(1,17),reverse=True):
                if 'd'+str(y) not in dr.keys():
                    dr['d'+str(y)] = drt[x]
                    break
        tlts = 0
        for ddrl in dr:
            tlts += float(dr[ddrl])
        if not dr.get('value'):
            dr['value'] = line.product_id.standard_price
        if not dr.get('total_value'):
            dr['total_value'] = tlts
        if not dr.get('total'):
            dr['total'] = tlts * line.product_id.standard_price
        
        # #compositional.information
        date_invoice = str(datetime.strptime(str(self.date_invoice)[0:10],'%Y-%m-%d') - timedelta(days=45))[0:10]
        #orders = self.env['purchase.order'].search([('partner_id','=',self.partner_id.id),('date_order','>=',date_purchase),('date_order','<=',str(date_invoice)[0:10])])
        #for order in orders:
        _logger.info('------')
        _logger.info(date_invoice)
        _logger.info(self.date_invoice)
        for qc in self.env['qc.inspection'].search([('state','=','success'),('date','>=',date_invoice),('date','<=',self.date_invoice)]):
            _logger.info(qc)
            if qc.object_id.id == self.partner_id.id:
                diff = (datetime.strptime(str(self.date_invoice)[0:10],'%Y-%m-%d') - datetime.strptime(str(qc.date)[0:10],'%Y-%m-%d')).days + 1
                _logger.info(diff)
                for lines in qc.inspection_lines:
                    if lines.test_line.name not in ci.keys():
                        ci[lines.test_line.name] = {'product_id':line.product_id.id,'qc_question_id':lines.test_line.id,'qna1':0,'qna2':0,'qna3':0,'avg':0}
                    if diff >0 and diff<=15:
                        ci[lines.test_line.name]['qna3'] += float(lines.quantitative_value)
                    elif diff > 15 and diff <=30:
                        ci[lines.test_line.name]['qna2'] += float(lines.quantitative_value)
                    else:
                        ci[lines.test_line.name]['qna1'] += float(lines.quantitative_value)
                    ci[lines.test_line.name]['avg'] = (ci[lines.test_line.name]['qna1'] + ci[lines.test_line.name]['qna2'] + ci[lines.test_line.name]['qna3'])/3
            _logger.info('------')
 
        self.mim_id = None
        self.dr_id = None
        self.ci_id = None
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
    accumulated = fields.Float(string='Accumulated',default=0.0)

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
    amount = fields.Float(string='Amount')
    code_python = fields.Text(string='Calc')


class DailyReception(models.Model):
    _name = "daily.reception"

    invoice_id = fields.Many2one('account.invoice',string='Invoice')
    value = fields.Float(string='Value', default=0.0)
    d1 = fields.Integer(string='Day 1', default=0)
    d2 = fields.Integer(string='Day 2', default=0)
    d3 = fields.Integer(string='Day 3', default=0)
    d4 = fields.Integer(string='Day 4', default=0)
    d5 = fields.Integer(string='Day 5', default=0)
    d6 = fields.Integer(string='Day 6', default=0)
    d7 = fields.Integer(string='Day 7', default=0)
    d8 = fields.Integer(string='Day 8', default=0)
    d9 = fields.Integer(string='Day 9', default=0)
    d10 = fields.Integer(string='Day 10', default=0)
    d11 = fields.Integer(string='Day 11', default=0)
    d12 = fields.Integer(string='Day 12', default=0)
    d13 = fields.Integer(string='Day 13', default=0)
    d14 = fields.Integer(string='Day 14', default=0)
    d15 = fields.Integer(string='Day 15', default=0)
    d16 = fields.Integer(string='Day 16', default=0)
    total_value = fields.Float(string='Total value', default=0.0)
    total = fields.Float(string='Total', default=0.0)
