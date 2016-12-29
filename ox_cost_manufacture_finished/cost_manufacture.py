# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductAttributeExtended(models.Model):
    _inherit = 'product.attribute'

    density = fields.Boolean(string='Density', default=False)
    fat = fields.Boolean(string='Fat', default=False)
    sng = fields.Boolean(string='S.N.G (%)', default=False)
    
class QCTestQuestionExtended(models.Model):
    _inherit = 'qc.test.question'

    density = fields.Boolean(string='Density', default=False)
    fat = fields.Boolean(string='Fat', default=False)
    sng = fields.Boolean(string='S.N.G (%)', default=False)

class StockMoveQualityControl(models.Model):
    _inherit = 'stock.move'

    inspection_id = fields.Many2one('qc.inspection',string='QC Inspection')

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

    def CalculateCost(self):
        fat_general, self.st, self.ov1, self.sng_percentage, self.st_percentage, self.gr_sl = 0, 0, 0, 0, 0, 0
        #Grasa producto terminado
        for att in self.product_id.attribute_value_ids:
            if att.attribute_id.fat:
                fat_general = float(att.name.replace(',','.'))
        #Valores materia prima
        sng, fat, density = 0, 0, 0
        for lines in self.move_raw_ids:
            for ins in lines.inspection_id.inspection_lines:
                if ins.test_line.sng:
                    sng = float(ins.quantitative_value)
                if ins.test_line.density:
                    density = float(ins.quantitative_value)
                if ins.test_line.fat:
                    fat = float(ins.quantitative_value)

            _logger.info("Fat General: %s"%str(fat_general))
            _logger.info("Fat: %s"%fat)
            _logger.info("Density: %s"%density)
            _logger.info("SNG: %s"%sng)
            # st
            self.st += fat + sng
            # ov1
            if not self.st:
                raise UserError("Dede definir la grasa o sólidos no grasos en la inspección.")
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
                _logger.info("Product: %s - Cost %s "%(bl.product_id,bl.product_id.standard_price))
                if bl.product_id.standard_price:
                    cost += bl.product_id.standard_price

            for sp in self.bom_id.sub_products:
                _logger.info("sub-producto: %s "%sp)
                for att in sp.product_id.attribute_value_ids:
                    if att.attribute_id.fat:
                        fat = float(att.name.replace(',','.'))
                sp.product_id.standard_price = (cost / (self.st/100))  * fat
                _logger.info("Cost: %s "%cost)
                _logger.info("fat: %s "%fat)
                _logger.info("sub-producto standard price: %s "%sp.product_id.standard_price)

            for fi in self.move_finished_ids:
                fi.price_unit = fi.product_id.standard_price
            for fi in self.move_raw_ids:
                fi.price_unit = fi.product_id.standard_price

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

