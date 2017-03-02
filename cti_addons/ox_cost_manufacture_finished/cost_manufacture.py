# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import math

_logger = logging.getLogger(__name__)

class ProductProductExtended(models.Model):
    _inherit = 'product.product'

    cost_special = fields.Boolean(string='Cost Special', default=False)

class ProductAttributeExtended(models.Model):
    _inherit = 'product.attribute'

    fat = fields.Boolean(string='Fat', default=False)

class QCTestQuestionExtended(models.Model):
    _inherit = 'qc.test.question'

    density = fields.Boolean(string='Density', default=False)
    fat = fields.Boolean(string='Fat', default=False)
    sng = fields.Boolean(string='S.N.G (%)', default=False)
    st = fields.Boolean(string='S.T ', default=False)
    protein = fields.Boolean(string='Protein', default=False)

class StockMoveQualityControl(models.Model):
    _inherit = 'stock.move'

    inspection_id = fields.Many2one('qc.inspection',string='QC Inspection')

class MRPRoutingWorkCenterCostExpected(models.Model):
    _inherit = 'mrp.routing.workcenter'

    @api.depends('default_cost','default_cost_per_labor')
    def _get_total(self):
        self.total_cost=self.default_cost+self.default_cost_per_labor

    default_cost = fields.Float(string='Default cost')
    default_cost_per_labor = fields.Float(string='Default cost per labor')
    total_cost = fields.Float(compute='_get_total', string='Total cost',store=False)

class MRPWorkorderCost(models.Model):
    _inherit = 'mrp.workorder'

    @api.depends('real_cost','real_cost_per_labor','duration')
    def _get_total(self):
        for x in self:
            x.total_cost=(x.real_cost+x.real_cost_per_labor)*x.duration

    default_cost = fields.Float(string='Default cost')
    default_cost_per_labor = fields.Float(string='Default cost per labor')
    real_cost = fields.Float(string='Real cost',required=True,default=0)
    real_cost_per_labor = fields.Float(string='Real cost per labor',required=True,default=0)
    total_cost = fields.Float(compute='_get_total', string='Total cost',store=False)

class CostManufacture(models.Model):
    _inherit = 'mrp.production'

    sng = fields.Float(string='SNG', default=0.0)
    st = fields.Float(string='ST', default=0.0)
    density = fields.Float(string='Density', default=0.0)
    ov = fields.Float(string='OV', default=1000)
    price_base = fields.Float(string='Price base', default=0.0)
    ov1 = fields.Float(string='OV1', default=0.0)
    sng_percentage = fields.Float(string='SNG (%)', default=0.0)
    st_percentage = fields.Float(string='ST (%)', default=0.0)
    gr_sl = fields.Float(string='GR S-L', default=0.0)
    standard_price = fields.Float(string='Cost', default=0.0)

    # @api.multi
    # def open_produce_product(self):
        
    #     return super(CostManufacture, self).open_produce_product()

    @api.multi
    def button_mark_done(self):
        _logger.info(self)
        self.CalculateCost()
        self.ensure_one()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self.post_inventory()
        moves_to_cancel = (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_to_cancel.action_cancel()
        self.write({'state': 'done', 'date_finished': fields.Datetime.now()})
        self.env["procurement.order"].search([('production_id', 'in', self.ids)]).check()
        self.write({'state': 'done'})

    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']
        bom_qty = bom_data['qty']

        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in bom.routing_id.operation_ids:
            # create workorder
            cycle_number = math.ceil(bom_qty / operation.workcenter_id.capacity)  # TODO: float_round UP
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'operation_id': operation.id,
                'duration_expected': duration_expected,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'default_cost': operation.default_cost,
                'default_cost_per_labor':operation.default_cost_per_labor,
                'capacity': operation.workcenter_id.capacity,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
            workorders += workorder

            # assign moves; last operation receive all unassigned moves (which case ?)
            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_lot_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders

    def CalculateCost(self):
        if self.product_id.cost_special:
            fat_general, self.st, self.ov1, self.sng_percentage, self.st_percentage, self.gr_sl = 0, 0, 0, 0, 0, 0
            #Grasa producto terminado
            for att in self.product_id.attribute_value_ids:
                if att.attribute_id.fat:
                    fat_general = float(att.name.replace(',','.'))
            #Valores materia prima
            sng, fat, fatc, density = 0, 0, 0,0
            for lines in self.move_raw_ids:
                for ins in lines.inspection_id.inspection_lines:
                    if ins.test_line.sng:
                        sng = float(ins.quantitative_value)
                    if ins.test_line.density:
                        density = float(ins.quantitative_value)
                    if ins.test_line.fat:
                        fat = float(ins.quantitative_value)
                        fatc += fat

                _logger.info("Fat General: %s"%str(fat_general))
                _logger.info("Fat: %s"%fat)
                _logger.info("Density: %s"%density)
                _logger.info("SNG: %s"%sng)
                # st
                self.st += fat + sng
                # ov1
                if self.st:
                    try:
                        self.ov1 += lines.product_id.standard_price / (density * self.st/100)
                    except ZeroDivisionError:
                        self.ov1 += 0.0
                    #sng_percentage
                    try:
                        self.sng_percentage += (sng*self.ov/100)/(self.ov-(fat-fat_general)*self.ov/100)*100
                    except ZeroDivisionError:
                        self.sng_percentage += 0.0
                    #st_percentage
                    self.st_percentage += self.sng_percentage + fat_general
                    # gr_sl
                    self.gr_sl += density * self.st_percentage/100

                    self.product_id.standard_price = self.gr_sl * self.ov1
                    cost = 0
                    for bl in self.bom_id.bom_line_ids:
                        if bl.product_id.standard_price:
                            cost += bl.product_id.standard_price
                    fats = 0
                    for sp in self.bom_id.sub_products:
                        for att in sp.product_id.attribute_value_ids:
                            if att.attribute_id.fat:
                                fat = float(att.name.replace(',','.'))/100
                                fats += fat
                        sp.product_id.standard_price = (cost / (self.st/100))  * fat
                    qty = abs((self.product_qty * (fat_general - fatc))/(fats*100-fatc))
                    for fi in self.move_finished_ids:
                        fi.price_unit = fi.product_id.standard_price
                        if fi.product_id != self.product_id:
                            fi.product_uom_qty = qty
                    for fi in self.move_raw_ids:
                        if fi.inspection_id:
                            fi.price_unit = fi.product_id.standard_price
                            _logger.info("fat_general: %s "%fat_general)
                            _logger.info("fatc: %s "%fatc)
                            _logger.info("fats: %s "%fats)
                            _logger.info("qty: %s "%self.product_qty)
                            fi.product_uom_qty += qty
        else:
            cost,cant,cant_t = 0,0,0
            for fi in self.move_raw_ids:
                if fi.product_uom_qty>0:
                    cost += fi.price_unit*fi.product_uom_qty
                    cant += fi.product_uom_qty
            cost_add = 0
            for ca in self.workorder_ids:
                cost_add += ca.total_cost
            #promedio
            cost = self.product_id.standard_price* self.product_id.qty_available
            cant = self.product_id.qty_available
            _logger.info('cant')
            _logger.info(self.product_id.name)
            _logger.info(cant)
            cost = cost / (cant or 1)
            for pf in self.move_finished_ids:
                cant_t += pf.product_uom_qty
            for pf in self.move_finished_ids:
                _logger.info('cant_t')
                _logger.info(cant_t)
                new_cost = cost * (pf.product_uom_qty/cant_t) + cost_add
                pf.product_id.standard_price = new_cost
                pf.price_unit = new_cost
        return True

    def _generate_finished_moves(self):
        _logger.info("Produccion, costo: ")
        _logger.info(self.product_id)
        self.CalculateCost()
        move = self.env['stock.move'].create({
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'product_id': self.product_id.id,
            'price_unit': self.product_id.standard_price,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'location_id': self.product_id.property_stock_production.id,
            'location_dest_id': self.location_dest_id.id,
            'move_dest_id': self.procurement_ids and self.procurement_ids[0].move_dest_id.id or False,
            'procurement_id': self.procurement_ids and self.procurement_ids[0].id or False,
            'company_id': self.company_id.id,
            'production_id': self.id,
            'origin': self.name,
            'group_id': self.procurement_group_id.id,
            })
        _logger.info(move)
        move.action_confirm()
        return move
