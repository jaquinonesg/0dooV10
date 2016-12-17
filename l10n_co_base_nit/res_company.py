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

from openerp import fields, models

class res_company(models.Model):
        _inherit = 'res.company'
        
        """_columns = {
            'vat_type': fields.related('partner_id', 'vat_type', string="Vat Type", type="char", size=32),
            'vat_vd': fields.related('partner_id', 'vat_vd', help='Digito de verificación', type="char", size=1),
            'company_registry': fields.char('Company Registry', size=64),
        }"""
        #vat_type = fields.Char(related='partner_id.vat_type', string="Vat Type",size=32)
        vat_type = fields.Selection([('12','12 - Tarjeta de identidad'), 
                                        ('13','13 - Cédula de ciudadanía'), 
                                        ('21','21 - Tarjeta de extranjería'),
                                        ('22','22 - Cédula de extranjería'), 
                                        ('31','31 - NIT (Número de identificación tributaria)'), 
                                        ('41','41 - Pasaporte'), 
                                        ('42','42 - Documento de identificación extranjero'), 
                                        ('43','43 - Sin identificación del exterior o para uso definido por la DIAN')],
                                        string='Tipo documento',
                                        help='Identificacion del Cliente, segun los tipos definidos por la DIAN. Si se trata de una persona natural y tiene RUT utilizar NIT',
                                        related='partner_id.vat_type')
        vat_vd = fields.Char(related='partner_id.vat_vd', string="Vat Type",size=1, help='Digito de verificación')
        company_registry = fields.Char('Company Registry', size=64)

        def write(self, values):
            """ Actualiza company_registry
                UPDATE res_company SET company_registry=b.ref FROM res_partner AS b WHERE b.id = partner_id
            """
            cr = self._cr
            uid = self.user_id.id
            ids = self.id
            context = self.env.context
            values['vat_type'] = '31'
            print values
            res = super(res_company, self).write(values)
            for company in self.browse(ids):
                if company.partner_id:
                    super(res_company, self).write({'company_registry': company.partner_id.ref2})
            
            return res
