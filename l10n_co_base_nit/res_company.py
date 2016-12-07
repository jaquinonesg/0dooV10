# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (c) 2011 OpenERP S.A. <http://openerp.com>
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

from openerp.osv import fields, osv

class res_company(osv.osv):
        _inherit = 'res.company'
        
        _columns = {
            'vat_type': fields.related('partner_id', 'vat_type', string="Vat Type", type="char", size=32),
            'vat_vd': fields.related('partner_id', 'vat_vd', help='Digito de verificación', type="char", size=1),
            'company_registry': fields.char('Company Registry', size=64),
        }

        def write(self, cr, uid, ids, values, context=None):
            """ Actualiza company_registry
                UPDATE res_company SET company_registry=b.ref FROM res_partner AS b WHERE b.id = partner_id
            """
            values['vat_type'] = '31'
            print values
            res = super(res_company, self).write(cr, uid, ids, values, context=context)
            for company in self.browse(cr, uid, ids, context=context):
                if company.partner_id:
                    super(res_company, self).write(cr, uid, [company.id], {'company_registry': company.partner_id.ref2}, context=context)
            
            return res
