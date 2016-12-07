# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from openerp import models, fields, api, _
from datetime import datetime,date
from openerp.exceptions import Warning, UserError
from openerp.tools.translate import _
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class sale_forecast(models.Model):
    _name = 'sale.forecast' 

    name = fields.Char('Name', required=True,track_visibility='onchange')
    period = fields.Selection([('week','Week'),('month','Month'),('quarter','Quarter'),('year','Year')],'Period', required=True, copy=False, default='week')
    period_count= fields.Integer('No. of Periods', required=True)
    start_date = fields.Date(string='Start Date',required=True, default=datetime.today())
    product_ids = fields.Char(string="Product") 
    forecast_product_ids = fields.One2many('forecast.product', 'forecast_id', string='Forecast Products', default=False)
    past_record_ids = fields.One2many('forecast.product', 'forecast_id', string='Past Forecast Records', default=False)
    past_sale_record_ids = fields.One2many('forecast.product', 'forecast_id', string='Past Sale Records', default=False)
    forecast_filter_id = fields.Many2one('forecast.period',string="Filter", edit=False)
    filter_visible = fields.Boolean('filter_visible' ,defalut=False)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse",select=True, required=True)
    create_action = fields.Boolean(string="Do you want to create Supply for process quantity?", default=False)
    required_process = fields.Selection([('buy','Buy'),('manufacture','Manufacture')],'Required Process', copy=False)
    record_generated = fields.Boolean('Record' ,defalut=False)
    state = fields.Selection([('open','Open'),('confirm','Confirm'),('done','Done')], copy=False, default='open')
    sales_person_id = fields.Many2one('res.users', string='Salesperson')
    past_forecast_records=fields.Boolean(string='Show Past Forecast Records')
    past_sales_records=fields.Boolean(string='Show Past Sales Records')

    # sales_team_id = fields.Many2one('crm.team', string='Sales Team')

    @api.one
    def set_confirm(self):
        return self.write({'state':'confirm'})

    @api.one
    def set_open(self):
        return self.write({'state':'open'})

    @api.v7
    def onchange_forecast_filter(self, cr, uid, ids, forecast_filter_id, context=None):
        f_period_obj = self.pool.get('forecast.period')
        f_product_obj = self.pool.get('forecast.product')
        if not ids:
            return {} 
        if forecast_filter_id:
            s_rec = f_product_obj.search(cr, uid, [('forecast_id','=',ids[0]),('period_start_date','=',f_period_obj.browse(cr, uid, forecast_filter_id,context ).p_date)])
            
        else:
            s_rec = f_product_obj.search(cr, uid, [('forecast_id','=',ids[0])], context)
        
        return {
            'value': {'forecast_product_ids': [(4,x) for x in s_rec]},
            'domain': {'forecast_product_ids': ['id' ,'in', s_rec]},
        }

    @api.v7
    def onchange_required_process(self, cr, uid, ids, required_process, context=None):

        forecast_product_obj = self.pool.get('forecast.product')
        if not ids:
            return {}
        line_list = []
        if not required_process:
            return {}
        if required_process:
            forecast_rec = self.browse(cr, uid, ids, context)
            for rec in forecast_rec:
                for line in rec.forecast_product_ids:
                    if line.action_required == 'none':
                        line_list.append((1, line.id, {'action_required': 'none'}))
                    else:    
                        line_list.append((1, line.id, {'action_required': required_process}))
        self.write(cr, uid, ids[0], {'forecast_product_ids': line_list}, context= context)
        return {'value': {'forecast_product_ids': line_list}}

    @api.v7
    def onchange_sales_person_id(self, cr, uid, ids, sales_person_id, context=None):

        forecast_product_obj = self.pool.get('forecast.product')
        if not ids:
            return {}

        line_sales_person = []
        forecast_rec = self.browse(cr, uid, ids, context)

        for rec in forecast_rec:
            for line in rec.forecast_product_ids:
                if sales_person_id:
                    line_sales_person.append((1, line.id, {'sales_person': sales_person_id}))
                else:
                    line_sales_person.append((1, line.id, {'sales_person': False}))
        self.write(cr, uid, ids[0], {'forecast_product_ids': line_sales_person}, context= context)
        return {'value': {'forecast_product_ids': line_sales_person}}

    @api.model
    def copy (self, default=None):
        raise Warning(_('Forecast Record Can not be Duplicated'))

    @api.model
    def create(self, vals):
        if vals.has_key('period_count'):
            if vals['period_count'] < 0:
                raise Warning(_('Number of Periods should not be less than zero'))
        return super(sale_forecast, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.has_key('forecast_filter_id'):
            vals['forecast_filter_id'] = False
        if vals.has_key('period_count'):
            if vals['period_count'] <= 0:
                raise Warning(_('Number of Periods should be grater than zero'))
        return super(sale_forecast,self).write(vals)

    @api.multi
    def get_period(self, period, start_date, period_count):
        res, period_list = [], []
        period_env = self.env['forecast.period']
        search_period_ids = period_env.search([('forecast_id', '=', self.id)])
        if search_period_ids:
            search_period_ids.unlink()
        if period == 'week':
            for item in range(period_count):
                week_date = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                res.append(week_date)
                new_week_date = week_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                new_start_date = datetime.strptime(new_week_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(weeks=1) + relativedelta(days=1)
                start_date = new_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif period == 'month':
            for item in range(period_count):
                month_date = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                res.append(month_date)
                new_month_date = month_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                new_start_date = datetime.strptime(new_month_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=1) + relativedelta(days=1)
                start_date = new_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif period == 'quarter':
            for item in range(period_count):
                quarter_date = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                res.append(quarter_date)
                new_quarter_date = quarter_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                new_start_date = datetime.strptime(new_quarter_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=3) + relativedelta(days=1)
                start_date = new_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif period == 'year':
            for item in range(period_count):
                year_date = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                res.append(year_date)
                new_year_date = year_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                new_start_date = datetime.strptime(new_year_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(years=1) + relativedelta(days=1)
                start_date = new_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        for start_date in res:
            vals = {
                'name': start_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'p_date': start_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'forecast_id': self.id
            }
            period_list.append(period_env.create(vals))
        self.filter_visible = True
        return period_list

    @api.multi
    def generate_forecast(self):
        action = False
        self.record_generated = True
        order_obj=self.env['sale.order']
        order_line_obj=self.env['sale.order.line']
        for rec in self:
            rec.write({'forecast_product_ids':[(5,0)]})
        forecast_product_obj = self.env['forecast.product']
        if self.period and self.start_date and self.period_count:
            periods = self.get_period(self.period, self.start_date, self.period_count)
        elif self.period_count <= 0:
            raise Warning(_('Number of Periods should be grater than Zero'))
        if self.product_ids:
            domain =  eval(self.product_ids)
            product_ids = self.env['product.product'].search(domain)
        else:
            raise Warning(_('Atleast one product should be selected!'))
        if not self.warehouse_id:
            raise Warning(_('Warehouse should be selected!'))
        first_period = True
        for index,item in enumerate(periods):
            if self.period == 'week':
                expected_end_date = datetime.strptime(item.name, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(weeks=1)
                end_date = expected_end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                previous_rec_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(weeks=1) - relativedelta(days=1)
                previous_rec_start_date = previous_rec_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                sec_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(weeks=2) - relativedelta(days=2)
                sec_last_start_date = sec_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                third_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(weeks=3) - relativedelta(days=3)
                third_last_start_date = third_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
            elif self.period == 'month':
                expected_end_date = datetime.strptime(item.name, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=1)
                end_date = expected_end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                previous_rec_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=1) - relativedelta(days=1)
                previous_rec_start_date = previous_rec_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                sec_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=2) - relativedelta(days=2)
                sec_last_start_date = sec_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                third_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=3) - relativedelta(days=3)
                third_last_start_date = third_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
            elif self.period == 'quarter':
                expected_end_date = datetime.strptime(item.name, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(months=3)
                end_date = expected_end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                previous_rec_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=3) - relativedelta(days=1)
                previous_rec_start_date = previous_rec_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                sec_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=6) - relativedelta(days=2)
                sec_last_start_date = sec_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                third_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months=9) - relativedelta(days=3)
                third_last_start_date = third_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
            elif self.period == 'year':
                expected_end_date = datetime.strptime(item.name, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(years=1)
                end_date = expected_end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                previous_rec_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(years=1) - relativedelta(days=1)
                previous_rec_start_date = previous_rec_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                sec_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(years=2) - relativedelta(days=2)
                sec_last_start_date = sec_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                third_last_period_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(years=3) - relativedelta(days=3)
                third_last_start_date = third_last_period_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
            for product in product_ids:
                product_template_id = product.product_tmpl_id
                routes = self.env['product.template'].search([('id','=',product_template_id.id)]).route_ids
                mto_route_id = self.env['stock.location.route'].search([('name','=','Make To Order')]).id
                if routes:
                    if routes.filtered(lambda r: r.id == mto_route_id):
                        action = 'none'
                    else:
                        if routes.filtered(lambda r: r.name == 'Buy') and routes.filtered(lambda r: r.name == 'Manufacture'):
                            action = 'both'
                        else:
                            for route in routes:
                                if route.name == 'Buy':
                                    action = 'buy'
                                elif route.name == 'Manufacture':
                                    action = 'manufacture'
                else:
                    action = 'none'
                ctx = self._context.copy()
                ctx.update({'from_date': item.name, 'to_date': end_date, 'warehouse': self.warehouse_id.id, 'current_model': self._model, 'rec_id': self.id})
                product_qty = self.pool.get('product.product')._product_available(self._cr, self._uid, [product.id], False, False, ctx)
                qty_list = product_qty.get(product.id)
                last_period_qty,sec_last_period_qty, third_last_period_qty, avg_qty = 0.0,0.0,0.0,0.0
                if first_period == True:
                    new_rest_period_qty = qty_list['qty_available']
                    available_qty = new_rest_period_qty
                    forecast_product_rec = self.env['forecast.product']
                    forecast_product_last_recs = forecast_product_rec.search([('period_start_date','=',previous_rec_start_date),('product_id','=',product.id)])
                    if forecast_product_last_recs:
                        last_period_qty = forecast_product_last_recs[0].forecast_qty
                    forecast_product_sec_last_recs = forecast_product_rec.search([('period_start_date','=',sec_last_start_date),('product_id','=',product.id)])
                    if forecast_product_sec_last_recs:
                        sec_last_period_qty = forecast_product_sec_last_recs[0].forecast_qty
                    forecast_product_third_last_recs = forecast_product_rec.search([('period_start_date','=',third_last_start_date),('product_id','=',product.id)])
                    if forecast_product_third_last_recs:
                        third_last_period_qty = forecast_product_third_last_recs[0].forecast_qty
                    if last_period_qty or sec_last_period_qty or third_last_period_qty:
                        avg_qty = (last_period_qty+sec_last_period_qty+third_last_period_qty)/3
                    previous_start_date = self.start_date
                    sale_qty=0.0
                    for i in range(1,12):
                        if self.period == 'week':
                            previous_new_rec_date = datetime.strptime(previous_start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(weeks = 1) - relativedelta(days=1)
                        elif self.period == 'month':
                            previous_new_rec_date = datetime.strptime(previous_start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months = 1) - relativedelta(days=1)
                        elif self.period == 'quarter':
                            previous_new_rec_date = datetime.strptime(previous_start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(months = 3) - relativedelta(days=1)
                        elif self.period == 'year':
                            previous_new_rec_date = datetime.strptime(previous_start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(years = 1) - relativedelta(days=1)
                        previous_new_rec_date = previous_new_rec_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                        order_recs = order_obj.search([('date_order','<=',previous_start_date),('date_order','>=',previous_new_rec_date)])
                        if order_recs:
                            for order_rec in order_recs:
                                order_line_recs = order_line_obj.search([('order_id','=',order_rec[0].id),('product_id','=',product.id)])
                                if order_line_recs:
                                    for order_line_rec in order_line_recs:
                                        sale_qty = sale_qty + order_line_rec.product_uom_qty
                        previous_start_date = previous_new_rec_date
                    if sale_qty:
                        avg_sale_qty = sale_qty/12
                    else:
                        avg_sale_qty=0.0
                else:
                    available_qty = 0.0

                vals = {
                    'name': product.name + ' on ' + str(item.name),
                    'forecast_id': self.id,
                    'product_id': product.id,
                    'period_start_date': item.name,
                    'period_end_date': end_date,
                    'onhand_qty': available_qty,
                    'last_period_qty': last_period_qty,
                    'sec_last_period_qty': sec_last_period_qty,
                    'third_last_period_qty': third_last_period_qty,
                    'incoming_qty': qty_list['incoming_qty'],
                    'outgoing_qty': qty_list['outgoing_qty'],
                    'rest_period_qty': available_qty,
                    'action_required': action,
                    'avg_qty':avg_qty,
                    'avg_sale_qty':round(avg_sale_qty or 0.0),

                }
                created_id = forecast_product_obj.create(vals)
            first_period = False

    @api.multi
    def update_action_qty(self):
        forecast_product_obj = self.env['forecast.product']
        if self.forecast_filter_id:
            recs = self.env['forecast.product'].search([('forecast_id','=',self.id),('period_start_date','=',self.forecast_filter_id.name)])
            self.forecast_filter_id = False
        else:
            recs = self.env['forecast.product'].search([('forecast_id','=',self.id)])
        for rec in recs:
            if not rec.forecast_qty and rec.avg_sale_qty:
                rec.forecast_qty = round(rec.avg_sale_qty)
            if not rec.onhand_qty:
                previous_period_date = rec.period_start_date
                new_date = datetime.strptime(previous_period_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=1)
                previous_period_end_date = new_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                new_rest_period_qty = self.env['forecast.product'].search([('product_id','=',rec.product_id.id),('period_end_date','=',previous_period_end_date),('forecast_id','=',self.id)]).action_qty
                if new_rest_period_qty < 0:
                    rec.rest_period_qty =  - (new_rest_period_qty)
                else:
                    rec.rest_period_qty = 0
            else:
                rec.rest_period_qty = rec.onhand_qty
            qty = rec.forecast_qty - (rec.rest_period_qty + rec.incoming_qty - rec.outgoing_qty)
            vals = {'action_qty': qty,'forecast_qty': rec.forecast_qty}
            if qty < 0:
                vals.update({'action_required':'none'})
            forecast_product_obj.browse(rec.id).write(vals)

    @api.multi
    def perform_action(self):
	location_id = False
        if self.create_action:
            if self.state != 'confirm':
                raise Warning(_('Forecast State should be Confirmed'))
            procurement_order_obj = self.env['procurement.order']
            supplier_obj = self.env['product.supplierinfo']
            res_company_obj = self.env['res.company']
            forecast_product_obj = self.env['forecast.product']

            for line in self.forecast_product_ids:
                line_product_id = line.product_id
                line_prod_temp_id = line.product_id.product_tmpl_id
                line_route_ids = self.env['product.template'].search([('id','=',line_prod_temp_id.id)]).route_ids 
                mto_route_id = self.env['stock.location.route'].search([('name','=','Make To Order')]).id

                company_id = line.product_id.company_id
                company_rec =  res_company_obj.search([('id','=',company_id.id)])
                if line_route_ids:
                    if not line_route_ids.filtered(lambda r: r.id == mto_route_id) and line.action_qty > 0 and line.action_required != 'none':
                        # To check whether type of product is Stockable
                        if line_prod_temp_id.type == 'product':
                            if line.action_required == 'buy':
                                route_id = self.env['stock.location.route'].search([('name','=','Buy')]).id
                                routes = route_id and [(4, route_id)] or []
                                picking_type_id = self.env['stock.warehouse'].search([('id','=',self.warehouse_id.id)]).in_type_id
                                location_id = self.env['stock.picking.type'].search([('id','=',picking_type_id.id)]).default_location_dest_id
                            elif line.action_required in ('manufacture','both'):
                                route_id = self.env['stock.location.route'].search([('name','=','Manufacture')]).id
                                routes = route_id and [(4, route_id)] or []
                                picking_type_id = self.env['stock.warehouse'].search([('id','=',self.warehouse_id.id)]).int_type_id
                                location_id = self.env['stock.picking.type'].search([('id','=',picking_type_id.id)]).default_location_dest_id

                            # routes = line_route_ids and [(4, line_route_ids.id)] or []
                            date_planned = datetime.strptime(line.period_start_date,DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=company_rec.security_lead)
                            procurement_date_planned = date_planned.strftime(DEFAULT_SERVER_DATE_FORMAT)
			    if not location_id:
                                UserError('Does not have a defined location, action required must be (buy,manufacture or both).')
                            vals = {
                                # 'product_uos_qty': 
                                'product_uom': line_prod_temp_id.uom_id.id,
                                'warehouse_id': self.warehouse_id.id,
                                'location_id': location_id.id,
                                'route_ids': routes,
                                'product_qty': line.action_qty,
                                # 'product_uos': line_prod_temp_id.uos_id,
                                'product_id': line_product_id.id,
                                'name': line_product_id.name,
                                'date_planned': procurement_date_planned,
                                'company_id': company_id.id,
                                'forecast_ref_procurement': self.id,
                            }
                            procurement_id = procurement_order_obj.create(vals).id
                            procurement_order_rec_state = procurement_order_obj.search([('id','=',procurement_id)]).state
                            if line.action_required == 'buy':
                                if procurement_order_rec_state == 'exception':
                                    document_number = 'Exception'    
                                elif procurement_order_rec_state == 'running':
                                    purchase_order_rec = procurement_order_obj.search([('id','=',procurement_id)]).purchase_id
                                    document_number = self.env['purchase.order'].search([('id','=',purchase_order_rec.id)]).name

                            elif line.action_required in ('manufacture','both'):
                                if procurement_order_rec_state == 'exception':
                                    document_number = 'Exception'    
                                elif procurement_order_rec_state == 'running':
                                    mrp_production_rec = procurement_order_obj.search([('id','=',procurement_id)]).production_id
                                    document_number = self.env['mrp.production'].search([('id','=',mrp_production_rec.id)]).name
                            forecast_product_obj.browse(line.id).write({'document_number': document_number, 'procurement_id': procurement_id})
                self.state ='done'


class product_product(models.Model):
    _inherit = 'product.product'    

    @api.multi
    def _get_domain_dates(self):
        for record in self:
            if (self._context.has_key('current_model') and self._context['current_model']) and (self._context.has_key('rec_id') and self._context['rec_id']):
                record_id = self._context['rec_id']
                generated_record = self.env['sale.forecast'].browse(record_id).record_generated
                if generated_record:
                    from_date = self._context.get('from_date', False)
                    to_date = self._context.get('to_date', False)
                    domain = []
                    if from_date:
                        domain.append(('date_expected', '>=', from_date))
                    if to_date:
                        domain.append(('date_expected', '<=', to_date))
                    return domain
        return super(product_product,self)._get_domain_dates()

class forecast_period(models.Model):

    _name = 'forecast.period'

    _rec_name = 'p_date'

    name = fields.Char('Period Name', edit=False)
    p_date = fields.Date('Period Date')
    forecast_id = fields.Many2one('sale.forecast', string='Forecast', edit=False)

class forecast_product(models.Model):

    _name = 'forecast.product'

    name = fields.Char('Name')
    forecast_id = fields.Many2one('sale.forecast', string='Forecast')
    product_id = fields.Many2one('product.product', string='Product')
    period_start_date = fields.Date('Start Date')
    period_end_date = fields.Date('End Date')
    sales_person = fields.Many2one('res.users', string='Salesperson')
    # sales_team = fields.Many2one('crm.team', string='Sales Team')
    forecast_qty = fields.Float('Forecast Qty')
    onhand_qty = fields.Float('Onhand Qty')
    rest_period_qty = fields.Float('Rest Period Qty')
    incoming_qty = fields.Float('Incoming Qty')
    outgoing_qty = fields.Float('Outgoing Qty')
    action_qty = fields.Float('Action Qty')
    document_number = fields.Char('Ref.Doc.No.')
    procurement_id = fields.Char('Procurement id')
    action_required = fields.Selection([('buy','Buy'),('manufacture','Manufacture'),('both','Both'),('none','Not Required')],'Action Required', copy=False)
    last_period_qty = fields.Float('Last Period Qty')
    sec_last_period_qty = fields.Float('Second Last Period Qty')
    third_last_period_qty = fields.Float('Third Last Period Qty')
    avg_qty = fields.Float("Average Forecast Qty")
    avg_sale_qty = fields.Float("Average Sale Quantity")


    @api.multi
    def unlink(self):
        '''
        Here as per the selection of forecast_filter_id the records other than the filter value are not managable as filter is applying on One2many field.
        so, by default unlink method is called for the records other than the filter records.
        To resolve this here unlink method is marked as false, as delete functionality has been removed  for this perticular field once the record is created.
        '''
        return False

class purchase_order(models.Model):
    _inherit = "purchase.order"

    forecast_ref_purchase = fields.Many2one('sale.forecast', string='Forecast Ref.')
# , domain=[('document','<>','view')]

class procurement_order(models.Model):

    _inherit = "procurement.order"

    forecast_ref_procurement = fields.Many2one('sale.forecast', string='Forecast ref')

    @api.v7
    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals, line_vals, context=None):
        if procurement.forecast_ref_procurement:
            po_vals.update({'forecast_ref_purchase': procurement.forecast_ref_procurement.id})
        return super(procurement_order, self).create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context)

    @api.v7
    def _prepare_mo_vals(self, cr, uid, procurement, context=None):
        vals = super(procurement_order, self)._prepare_mo_vals(cr, uid, procurement, context)
        if procurement.forecast_ref_procurement:
            vals.update({'forecast_ref_mrp' : procurement.forecast_ref_procurement.id})
        return vals

class mrp_production(models.Model):
    _inherit = 'mrp.production'

    forecast_ref_mrp = fields.Many2one('sale.forecast', string='Forecast Ref.')
