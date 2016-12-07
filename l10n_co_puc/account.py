# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
import openerp.addons.decimal_precision as dp
from openerp.osv import fields,osv

import logging

_logger = logging.getLogger('openerp.3RP')



class account_chart_template(osv.osv):
    """
    Adiciona los campos necesarios para tener como default en entradas y salidas de inventario, asi como la valoracion
    """
    _inherit = "account.chart.template"

    _columns={
#        'property_stock_account_output_categ': fields.many2one('account.account.template', 'Stock Output Account'),
#        'property_stock_account_input_categ': fields.many2one('account.account.template', 'Stock Input Account'),
        'property_stock_valuation_account_id': fields.many2one('account.account.template', 'Stock Valuation Account'),
    }


    
class account_tax_template(osv.osv):
    _name = 'account.tax.template'
    _inherit = 'account.tax.template'

    _columns = {
        'counterpart': fields.boolean('Incluir contrapartida', help="Impuesto que no se reflejara en la factura, utilizado regularmente para aprovisionamiento."),
        'counterpart_tax_id': fields.many2one('account.tax.template', 'Taxes', help="The TAX account used for this taxes."),
        'partner_id': fields.many2one('res.partner', 'Partner'  ),
        'sale_include': fields.boolean(u'Incluir impuesto de la cotización', help=u"Impuesto que se reflejara en la cotización."),
        'active_template': fields.boolean('active_template', help="If the active_template field is set to False"),
    }


    _defaults = {
        'counterpart': False,
        'sale_include': False,
        'active_template': True,
    }
    

class account_tax(osv.osv):
    _name = 'account.tax'
    _inherit = 'account.tax'

    _columns = {
        'counterpart': fields.boolean('Incluir contrapartida', help="Impuesto que no se reflejara en la factura, utilizado regularmente para aprovisionamiento."),
        'counterpart_tax_id': fields.many2one('account.tax', 'Taxes', help="The TAX account used for this taxes."),
        'partner_id': fields.many2one('res.partner', 'Partner'  ),
        'sale_include': fields.boolean(u'Incluir impuesto de la cotización', help=u"Impuesto que se reflejara en la cotización."),
    }


    _defaults = {
        'counterpart': False,
        'sale_include': False,
    }


class account_tax_code_template(osv.osv):
    _name = "account.tax.code.template"
    _inherit = "account.tax.code.template"
    
    _columns = {
            'python_invoice': fields.text('Invoice Python Code',help='Python code to apply or not the tax at invoice level'),
            'applicable_invoice': fields.boolean('Applicable Invoice', help="Use python code to apply this tax code at invoice. This funcionality doesn't aplly to refound invoices."),
            'key': fields.integer('Sort key'),
            'active_template': fields.boolean('active_template', help="If the active_template field is set to False"),
        }

    _defaults = {
            'python_invoice': '''# amount\n# base\n# fiscal_unit\n# invoice: account.invoice object or False\n# partner: res.partner object or None\n# table: base.element object or None\n\n#result = table.get_element_percent(cr,uid,'COD_TABLE','COD_ELEMENT')/100\n#result = base > fiscal_unit * 4\n\nresult = True''',
            'applicable_invoice': False,
            'active_template': True,
        }

    _order = 'key'
        
        
class account_tax_code(osv.osv):
    _name = "account.tax.code"
    _inherit = "account.tax.code"
    
    _columns = {
            'python_invoice': fields.text('Invoice Python Code',help='Python code to apply or not the tax at invoice level'),
            'applicable_invoice': fields.boolean('Applicable Invoice', help="Use python code to apply this tax code at invoice. This funcionality doesn't aplly to refound invoices."),
            'key': fields.integer('Sort key'),
            'active': fields.boolean('active_template', help="If the active_template field is set to False"),
        }

    _defaults = {
            'python_invoice': '''# amount\n# base\n# fiscal_unit\n# invoice: account.invoice object or False\n# partner: res.partner object or None\n# table: base.element object or None\n\n#result = table.get_element_percent(cr,uid,'COD_TABLE','COD_ELEMENT')/100\n#result = base > fiscal_unit * 4\n\nresult = True''',
            'applicable_invoice': False,
            'active': True,
        }
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
