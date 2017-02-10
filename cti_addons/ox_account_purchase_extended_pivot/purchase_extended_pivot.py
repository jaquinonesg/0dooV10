# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp import tools

class PurchaseAnalysis(models.Model):
    _name = 'purchase.analysis'
    _auto = False

    state_id = fields.Many2one('res.country.state', string='State')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Partner')
    order_id = fields.Many2one('purchase.order', string='Order')
    product_qty = fields.Integer(string='Quantity')
    qty_received = fields.Integer(string='Quantity received')
    qty_invoiced = fields.Integer(string='Quantity invoiced')
    price_subtotal = fields.Float(string='Price subtotal')
    price_tax = fields.Float(string='Price tax')
    price_total = fields.Float(string='Price total')
    qc_name = fields.Char(string='Quality control')
    quantitative_value = fields.Float(string='Quantitative value')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        #groupby_fields = set([groupby] if isinstance(groupby, basestring) else groupby)
        #if groupby_fields.intersection(USER_PRIVATE_FIELDS):
        #    raise AccessError(_("Invalid 'group by' parameter"))
        return super(PurchaseAnalysis, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model_cr
    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'purchase_analysis')
        cr.execute("""
            CREATE OR REPLACE VIEW purchase_analysis AS
                SELECT  row_number() OVER () AS id, 
                    rcs.id as state_id, 
                    rp.id as partner_id, 
                    po.id as order_id, 
                    pol.product_id as product_id,
                    pol.product_qty,
                    pol.qty_received, 
                    pol.qty_invoiced, 
                    pol.price_subtotal,
                    pol.price_tax,
                    pol.price_total,
                    qtq.name as qc_name,
                    qil.quantitative_value
                    FROM purchase_order_line pol
                        INNER JOIN purchase_order po ON po.id = pol.order_id
                        INNER JOIN res_partner rp ON rp.id = po.partner_id
                        INNER JOIN res_country_state rcs ON rcs.id = rp.state_id
                        LEFT JOIN qc_inspection qi ON object_id like 'purchase.order%' AND replace(object_id,'purchase.order,','')::integer = po.id
                        LEFT JOIN qc_inspection_line qil ON qil.inspection_id = qi.id
                        LEFT JOIN qc_test_question qtq ON qtq.id = test_line;
			ALTER TABLE purchase_analysis
  				OWNER TO odoo; """)
