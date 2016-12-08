# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#from odoo import api, fields, models, tools
#from odoo.fields import Datetime as fieldsDatetime
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp import tools

class CostManufacture(models.Model):
    _name = 'cost.manufacture'
    _auto = False

    mrp_id = fields.Many2one('mrp.production', string='Production')
    product = fields.Many2one('product.product', string='Product')

    planned_uom = fields.Many2one('product.uom', string='Planned Uom')
    planned_qty = fields.Float(string='Planned qty',default=0)
    unit_cost = fields.Float(string='Unit cost',default=0)
    planned_cost_total = fields.Float(string='Planned cost total', default=0)

    cons_qty = fields.Float(string='Consumed qty',default=0.0)
    cons_cost_total = fields.Float(string='Consumed cost total', default=0.0)

    prod_qty = fields.Float(string='Produced qty',default=0.0)
    prod_cost = fields.Float(string='Product cost',default=0)
    prod_uom = fields.Many2one('product.uom', string='Produced Uom')
    prod_cost_total = fields.Float(string='Produced cost total',default=0.0)
    diff_qty_total = fields.Float(string='Total diff qty', default=0.0)
    diff_cost_total = fields.Float(string='Total diff cost', default=0.0)
    porc_cost_total = fields.Float(string='% diff cost', default=0.0)

    state = fields.Selection([('confirmed', 'Confirmed'), 
                                ('planned', 'Planned'), 
                                ('progress', 'Progress'),
                                ('cancel', 'Cancel'), 
                                ('done', 'Done')
    ])

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        #groupby_fields = set([groupby] if isinstance(groupby, basestring) else groupby)
        #if groupby_fields.intersection(USER_PRIVATE_FIELDS):
        #    raise AccessError(_("Invalid 'group by' parameter"))
        return super(CostManufacture, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model_cr
    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'cost_manufacture')
        cr.execute("""
            CREATE OR REPLACE VIEW cost_manufacture AS 
    SELECT *,
        abs(cons_qty-planned_qty) AS diff_qty_total,
        abs(cons_cost_total-planned_cost_total) AS diff_cost_total,
        abs((cons_cost_total-planned_cost_total)/CASE WHEN  planned_cost_total<1 THEN 1 ELSE planned_cost_total END)*100 AS porc_cost_total
        FROM (
            SELECT row_number() OVER () AS id,
                datos.mrp_id,
                datos.state,
                datos.product,
                datos.planned_uom,
                sum(datos.planned_qty) AS planned_qty,
                sum(datos.cons_price) AS unit_cost,
                sum(datos.planned_qty)::double precision * sum(datos.cons_price) AS planned_cost_total,
                sum(datos.cons_qty) AS cons_qty,
                sum(datos.cons_price) * sum(datos.cons_qty)::double precision AS cons_cost_total,
                datos.prod_uom,
                sum(datos.prod_qty) AS prod_qty,
                SUM(datos.prod_price) AS prod_cost,
                SUM(datos.prod_price) * sum(datos.prod_qty)::double precision AS prod_cost_total
                FROM (  
                    SELECT mp.id AS mrp_id,
                        mp.state,
                        cons.product_id AS product,
                        cons.product_uom AS planned_uom,
                        SUM(cons.product_uom_qty) AS planned_qty,
                        SUM(cons.ordered_qty) AS cons_qty,
                        cons.price_unit AS cons_price,
                        0 AS prod_uom,
                        0 AS prod_qty,
                        0 AS prod_price
                            FROM mrp_production mp
                            LEFT JOIN stock_move cons ON cons.raw_material_production_id = mp.id
                                GROUP BY mp.id, mp.state, cons.product_id, cons.product_uom, cons.price_unit
                    UNION
                    SELECT mp.id AS mrp_id,
                        mp.state,
                        prod.product_id AS product,
                        0 AS planned_uom,
                        SUM(prod.product_uom_qty) AS planned_qty,
                        0 AS cons_qty,
                        0 AS cons_price,
                        prod.product_uom AS prod_uom,
                        SUM(prod.ordered_qty) AS prod_qty,
                        prod.price_unit AS prod_price
                            FROM mrp_production mp
                            LEFT JOIN stock_move prod ON prod.production_id = mp.id
                            GROUP BY mp.id, mp.state, prod.product_id, prod.product_uom, prod.price_unit
                ) as datos
                GROUP BY datos.mrp_id, datos.state, datos.product, datos.planned_uom, datos.prod_uom
            ) as todo;
ALTER TABLE cost_manufacture
  OWNER TO odoo;
		""")
