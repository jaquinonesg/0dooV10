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

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

class hr_payslip_employees(models.TransientModel):
    _inherit ='hr.payslip.employees'
    
    '''def _get_period(self, dt=None):
        period_obj = self.env['account.period']
        period_id = period_obj.search([()])
        if period_id:
            return period_id[0]
        return False
        
    def _get_default_period(self):
        return self._get_period(dt=None)    '''
        
'''    def compute_sheet(self):
        res = super(hr_payslip_employees, self).compute_sheet()
        context= self.env.context
        emp_pool = self.env['hr.employee']
        run_pool = self.env['hr.payslip.run']
        _logger.info(run_pool)
        _logger.info(self)
        run_data = run_pool.read(['date_start', 'date_end'])
            
        #date_start = run_data.get('date_start', False)
        #if date_start:
            #period_id = self._get_period(sdt=date_start)
        #if period_id: 
            #context.update({'period_id': period_id})
        data = self.read(context=context)[0]
        for emp in emp_pool.browse(data['employee_ids']):
            if not emp.contract_id:
                raise UserError("El empleado %s no tiene 'Contrato'"% emp.name)
            if not emp.address_home_id:
                raise UserError("El empleado %s no tiene 'Empleado / Tercero'"%emp.name)
            if not emp.contract_id.struct_id:
                raise UserError("El contrato de %s no tiene 'Estructura Salarial'"% emp.name)
            if not emp.contract_id.working_hours:
                raise UserError("El contrato de %s no tiene 'Planificación de Trabajo'"%emp.name)
                
        return res'''

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
