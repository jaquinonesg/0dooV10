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

from openerp.osv import fields, osv
from openerp.tools.misc import ustr
from openerp.tools.translate import _

class res_partner(osv.osv):

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


    def get_ref(self, cr, uid, ids,context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = []
        for records in self.browse(cr, uid, ids):
            if records.vat_type == '31':
                vat = records.vat[:3] + '.' + records.vat[3:6] + '.' + records.vat[6:9] + '-' + records.vat_vd 
            else:
                vat = records.vat

            res.append((records['id'], vat))
            print(self)
        return res
    
    def _get_ref(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_ref(cr, uid, ids, context=context)
        return dict(res) 
        
    _columns = {
        'vat_type': fields.selection( (
                                        ('12','12 - Tarjeta de identidad'), 
                                        ('13','13 - Cédula de ciudadanía'), 
                                        ('21','21 - Tarjeta de extranjería'),
                                        ('22','22 - Cédula de extranjería'), 
                                        ('31','31 - NIT (Número de identificación tributaria)'), 
                                        ('41','41 - Pasaporte'), 
                                        ('42','42 - Documento de identificación extranjero'), 
                                        ('43','43 - Sin identificación del exterior o para uso definido por la DIAN')), u'Tipo de Documento',  
                                        help=u'Identificacion del Cliente, segun los tipos definidos por la DIAN. Si se trata de una persona natural y tiene RUT utilizar NIT'),
        'vat_vd': fields.char('vd', size=1, help='Digito de verificación'),
        'ref' : fields.function(_get_ref, type='char', string='NIF', store=True ),
    }

    _defaults = {
        'is_company': True,
        'vat_type': '31',
    }

    def check_vat_co(self, vat, vat_vd):
 
            # For new TVA numbers, do a mod11 check
        factor = ( 41, 37, 29, 23, 19, 17, 13, 7, 3 )
        csum = sum([int(vat[i]) * factor[i] for i in range(9)])
        check = csum % 11
        if check > 1:
            check = 11 - check
        return check == int(vat_vd)
        return False
        
    def onerror_msg(self, msg):
        return {'warning': {'title': _('Error!'), 'message': _(msg)}}

    def onchange_vat_type(self, cr, uid, ids, vat_type, context=None):
        return {'value': {'is_company': vat_type == '31'}}

    def onchange_vat(self, cr, uid, ids, vat_type, vat, vat_vd, context=None):
        
        msg_error = ''
        
        # Validaciones
        if not vat.isdigit() and vat_type != '41':
            return self.onerror_msg( u'Solo se aceptan numeros en la identificación')
            
        if len(vat) < 6:
            return self.onerror_msg( u'La identificación debe tener al menos 6 digitos')

        if vat_type == '31' and len(vat) != 9:
            return self.onerror_msg( u'La identificación debe tener 9 digitos para compañia')

        if vat_type == '31' and not self.check_vat_co(vat, vat_vd):
            return self.onerror_msg( u'Dígito de verificación incorrecto, corrijalo para poder continuar')
        
        if vat_type != '31':
            return {'value': {'vat_vd': ''}}
            
            
        return True
    
       
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
