#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import time
import calendar

from dateutil import parser

from openerp import netsvc
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from openerp import models
from openerp.tools import config
from openerp.tools.translate import _

import logging

_logger = logging.getLogger('3RP')

class hr_payslip_run(models.Model):

    _inherit = 'hr.payslip.run'
    
    def onchange_payslip(self):
        
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
        """ Actualiza journal
        """
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id or False 
        journal_id = self.pool.get('account.journal').search(cr, uid, [('code','=ilike','NOM'), ('company_id','=',company_id)], context=context)[0] or False        
        res = {'value':{
                    'journal_id': journal_id,
                }
              }
        
        return res
        
    def confirm_payslip_run(self):

        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
        slip_obj = self.pool.get('hr.payslip')
        for run in self.browse(cr, uid, ids, context=context):
            if run.state == 'draft':
                for slip in run.slip_ids:
                    if slip.state == 'draft':
                        slip_obj.process_sheet(cr, uid, [slip.id], context=context)
                self.close_payslip_run(cr, uid, ids, context=context)
        return True        
        
class hr_payslip(models.Model):
    '''
    Pay Slip
    '''
    _inherit = 'hr.payslip'

#    def compute_sheet(self, cr, uid, ids, context=None):

#        for payslip in self.browse(cr, uid, ids, context=context):

#            slip_data = self.onchange_employee_id(cr, uid, [], payslip.date_from, payslip.date_to, payslip.employee_id.id, payslip.contract_id.id, context=context)
#            res = {
#                'period_id': slip_data['value'].get('period_id', False),
#            }
#            self.write(cr, uid, [payslip.id], res, context=context)

#        return super(hr_payslip, self).compute_sheet(cr, uid, ids, context=context)
    
    
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        Se sobre escribe esta funcion para adicionar el CODE en la regla y poder usarlo en los calculos        
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
        
        def _get_code_holidays_status(name):
            holidays_status_pool = self.pool.get('hr.holidays.status')
            id = holidays_status_pool.search(cr, uid, [('name','ilike', name)])[0]
            
            return holidays_status_pool.browse(cr, uid, id).code or name

        res = super(hr_payslip, self).get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context)
        d = parser.parse(date_from)

        last_day_of_month = calendar.monthrange(d.year, d.month)[1]
        working_days = 0.0
        leaves_days = 0.0

        """
            compute_30 = (days_work100 == last_day_of_month) and 30.0 or days_work100

            if (days_work100 + extended_leave) == last_day_of_month:
                compute_30 = 30.0 - extended_leave        
        """
        
        for k in res:
            k['number_of_days'] = (k['number_of_days'] == last_day_of_month) and 30.0 or k['number_of_days']
            if  k['code'] == 'WORK100':
                working_days += k['number_of_days']
            else:
                leaves_days += k['number_of_days']
                k['code'] = _get_code_holidays_status(k['name'])
            

        # Reasigna valor de dias en funcion de 30
        compute_30 = ((working_days == last_day_of_month) and 30.0 or False) or (((working_days + leaves_days) == last_day_of_month) and (30.0 - leaves_days) or False) or working_days
 
        for k in res:
            if  k['code'] == 'WORK100':
                k['number_of_days'] = compute_30
                k['number_of_hours'] = compute_30 * 8.0
                
        print res

        return res
        
       
    def hr_verify_sheet(self):
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
        for payroll in self.browse(cr, uid, ids, context=context):
            if not payroll.employee_id.address_home_id:
                raise except_orm(
                    _('Warning'), _('This employee don´t have a home address'))
            if not payroll.contract_id.working_hours:
                raise except_orm(
                    _('Warning'), _('This employee don´t have a working hours'))
        return super(hr_payslip, self).hr_verify_sheet(cr, uid, ids)    
        
        
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        
        """ Actualiza periodo
        """
        
        #period_pool = self.pool.get('account.period')
        #res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id, contract_id, context=context)
        #ctx = dict(context or {}, account_period_prefer_normal=True)
        #search_periods = period_pool.find(cr, uid, date_to, context=ctx)
        #res['value'].update({'period_id': search_periods[0]})
        #return res        
	pass
        
    def onchange_contract_id(self, date_from, date_to, employee_id=False, contract_id=False):
        
        """ Actualiza journal en los slip
        """
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
        
        res = super(hr_payslip, self).onchange_contract_id(cr, uid, ids, date_from, date_to, employee_id=employee_id, contract_id=contract_id, context=context)
        if not res['value']['journal_id'] and contract_id:
            contract = self.pool.get('hr.contract').browse(cr, uid, contract_id, context=context)
            journal_id = self.pool.get('account.journal').search(cr, uid, [('code','=ilike','NOM'), ('company_id','=',contract.employee_id.company_id.id)], context=context)[0] or False
            res['value'].update({'journal_id': journal_id})
        return res
       
    def process_sheet(self):
        
        """ Buscar en account_move_line las lineas con account payable y que pertenezcan a el salary_rule a cambiar el partner y actualizarlas
        """
        cr = self._cr
        uid = self.env.user_id.id
        ids = self.id
        context= self.env.context
        
        # Actualiza con el nivel superior la funcion
        res = super(hr_payslip, self).process_sheet(cr, uid, ids, context=context)
        slip_line_pool = self.pool.get('hr.payslip.line')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        
        # Busca el payslip
        for slip in self.browse(cr, uid, ids, context=context):
            _logger.debug("\n Slip %s\n" % (slip))
                
            move_id = account_move_obj.browse(cr, uid, slip.move_id.id, context=context)
            
            if move_id and slip.contract_id and slip.contract_id.employee_id and slip.contract_id.employee_id.address_home_id:
                account_move_obj.write(cr, uid, [move_id.id],  {'partner_id': slip.contract_id.employee_id.address_home_id.id, 'name': slip.name}, context)
            
                register_name = []
                # Genera una lista para una facil comprovacion
                for register in slip.contract_id.contrib_register_ids:
                    register_name.append(register.contrib_id.name)
                
                _logger.debug("\n Name Rule %s\n" % (register_name))
                # Recorre el asiento contable
                for move_line in move_id.line_id:
                    _logger.debug("\n Name Move %s\n" % (move_line.name))
                    # Actualiza la acount_move_line con el ID del empleado
                    account_move_line_obj.write(cr, uid, [move_line.id], {'partner_id': slip.contract_id.employee_id.address_home_id.id}, context)
                    # Compueba que la cuenta sea una payable y que el nombre del spip coincida con la regla salarial
                    slip_line_ids = slip_line_pool.search(cr, uid, [('slip_id','=', slip.id)])
                    for slip_line in slip_line_pool.browse(cr, uid, slip_line_ids):
                        if slip_line.salary_rule_id and slip_line.salary_rule_id.register_id and move_line.name == slip_line.name:
                            _logger.debug("\n Para Cambiar %s\n" % (move_line.name))
                            # Como al menos uno de los nombres coincide.. actualiza la linea
                            for register in slip.contract_id.contrib_register_ids:
                                if register.contrib_id.id == slip_line.salary_rule_id.register_id.id:
                                    partner_id = register.partner_id and register.partner_id.id or False
                                    account_move_line_obj.write(cr, uid, [move_line.id], {'partner_id': partner_id}, context)
        return res


