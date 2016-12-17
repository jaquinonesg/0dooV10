# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 OpenERP SA (<http://openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import string
import datetime
import re
_logger = logging.getLogger(__name__)

from openerp import fields, models
from openerp.tools.misc import ustr
from openerp.tools.translate import _

class res_partner(models.Model):

        _inherit = 'res.partner'
        
        """
                        Tipo de documento: Lista de selección con los tipos de documento aceptados por la autoridad de impuestos (DIAN).  
                    11 - Registro civil
                    12 - Tarjeta de identidad
                    13 - Cédula de ciudadanía
                    21 - Tarjeta de extranjería
                    22 - Cédula de extranjería
                    31 - NIT (Número de identificación tributaria)
                    41 - Pasaporte
                    42 - Tipo de documento extranjero
                    43 - Para uso definido por la DIAN 
                    
                    http://www.dian.gov.co/descargas/normatividad/Factura_Electronica/Anexo_001_R14465.pdf
        """

            
        def _get_ref(self, _field_name, _args):
            cr = self._cr
            uid = self.user_id.id
            ids = self.id
            result = dict.fromkeys(ids, False)
            for partner in self.browse(ids):
                
                if partner.vat and partner.vat_type == '31' and len(partner.vat) == 9 and partner.vat_vd:
                    result[partner.id] = partner.vat[:3] + '.' + partner.vat[3:6] + '.' + partner.vat[6:9] + '-' + partner.vat_vd 
                else:
                    result[partner.id] = partner.vat
                    
                self.write({'ref': result[partner.id]})       
                    
            return result
            
        """_columns = {
            'vat_type': fields.selection( (
                                            ('12',u'12 - Tarjeta de identidad'), 
                                            ('13',u'13 - Cédula de ciudadanía'), 
                                            ('21',u'21 - Tarjeta de extranjería'),
                                            ('22',u'22 - Cédula de extranjería'), 
                                            ('31',u'31 - NIT (Número de identificación tributaria)'), 
                                            ('41',u'41 - Pasaporte'), 
                                            ('42',u'42 - Documento de identificación extranjero'), 
                                            ('43',u'43 - Sin identificación del exterior o para uso definido por la DIAN')), u'Tipo de Documento',  
                                            help=u'Identificacion del Cliente, segun los tipos definidos por la DIAN. Si se trata de una persona natural y tiene RUT utilizar NIT'),
            'vat_vd': fields.char('vd', size=1, help='Digito de verificación'),
            'ref2': fields.function(_get_ref, type='char', string='NIF2', store=False ),
        }"""
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
                                        default='31')
        vat_vd = fields.Char(string='vd',size=1, help='Digito de verificación')
        ref2 = fields.Char(compute='_get_ref', string='NIF2', store=True )

#        _defaults = {
#            'is_company': True,
#        }


        def check_vat_co(self, vat_type, vat, vat_vd):
            # For new TVA numbers, do a mod11 check
            if vat_type != '31':
                return True
                
            if not vat_vd or len(vat_vd) != 1:
                return False
                
            factor = ( 41, 37, 29, 23, 19, 17, 13, 7, 3 )
            csum = sum([int(vat[i]) * factor[i] for i in range(9)])
            check = csum % 11
            if check > 1:
                check = 11 - check
            return check == int(vat_vd)
            return False
            
        def onerror_msg(self, msg):
            return {'warning': {'title': _('Error!'), 'message': _(msg)}}

        def onchange_vat_type(self,vat_type):
            return {'value': {'is_company': vat_type == '31'}}

        def onchange_vat(self, vat_type, vat, company_id):
            
            # Validaciones
            if not vat_type:
                return True
                
            if not vat:
                return self.onerror_msg( u'La identificación NO debe tener seer NULA, rectifique')

            if len(vat) < 6:
                return self.onerror_msg( u'La identificación debe tener al menos 6 digitos, rectifique')

            if not vat.isdigit() and vat_type != '41':
                return self.onerror_msg( u'Solo se aceptan numeros en la identificación, rectifique')

            if vat_type != '31':
                return {'value': {'vat_vd': ''}}                
                
            if len(vat) != 9:
                return self.onerror_msg( u'La identificación debe tener 9 digitos para compañia')            
            
            return True

        def onchange_vat_vd(self, vat_type, vat, vat_vd):
            if vat_type == '31':
                if not vat_vd:
                    return self.onerror_msg( u'El dígito de verificación NO debe tener seer NULO, rectifique')                
                    
                if not self.check_vat_co(vat_type, vat, vat_vd):
                    return self.onerror_msg( u'NIT suministrado no supera la prueba del dígito de verificacion!')
            
            return True            

        def _commercial_fields(self):
            """ Returns the list of fields that are managed by the commercial entity
            to which a partner belongs. These fields are meant to be hidden on
            partners that aren't `commercial entities` themselves, and will be
            delegated to the parent `commercial entity`. The list is meant to be
            extended by inheriting classes. """
            return ['website']

        def copy(self, default=None):
            partner_dic = self.read(['name','vat',])
            default = default or {}
            default.update({
                'name': '(copy) ' + partner_dic['name'],
                'vat': '(copy) ' + partner_dic['vat'],
            })
            return super(res_partner, self).copy(default)
            
            
        def _check_vat(self):
            cr = self._cr
            uid = self.user_id.id
            ids = self.id
            
            obj = self
            if obj.company_id and obj.vat and self.search([('company_id','=',obj.company_id.id),('vat','=ilike',obj.vat),('parent_id','=', None)]) != ids:
                return False
            return True
            
        def _check_vat_vd(self):
            cr = self._cr
            uid = self.user_id.id
            ids = self.id
            
            obj = self.browse(ids[0])
            if obj.vat_type == '31' and not self.check_vat_co(obj.vat_type, obj.vat, obj.vat_vd):
                return False
            return True
            
        #_constraints = [
        #    (_check_vat, u'\n\n NIT suministrado ya existe!', ["vat",]),
        #    (_check_vat_vd, u'\n\n NIT suministrado no supera la prueba del dígito de verificacion!', ["vat_vd",]),
        #]
        
        _sql_constraints = [
            ('code_name_uniq', 'unique (company_id,name)', u'Nombre de Cliente/Proveedor debe ser unico por compañia !')
        ]   
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


        
