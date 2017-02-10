# -*- coding: utf-8 -*-

from odoo import models, fields, api
#from odoo.exceptions import UserError
import logging
#from datetime import date, datetime, timedelta
#import time
#import pytz

_logger = logging.getLogger(__name__)

class HRApplyTemplate(models.TransientModel):
    _inherit = 'hr.payroll.config.settings'

    @api.multi
    def apply_hr_template(self):
        _logger.info('INIT method apply_hr_template')
        if not self.env.user.company_id.chart_template_id:
            raise UserError('You must define a chart of accounts for the company')
        #hr.contribution.register.template
        _logger.info('hr.contribution.register.template')
        hcrt = self.env['hr.contribution.register.template'].search([])
        for register in hcrt:
            self.env['hr.contribution.register'].create({'name':register.name,
                        'company_id':self.env.user.company_id.id,
                        'note':register.note})

        #hr.salary.rule.category.template
        _logger.info('hr.salary.rule.category.template')
        hsrct = self.env['hr.salary.rule.category.template'].search([])
        for register in hsrct:
            self.env['hr.salary.rule.category'].create({'code':register.code,
                        'name':register.name,
                        'company_id':self.env.user.company_id.id,
                        'note':register.note,
                        'parent_id':register.parent_id.id})

        #hr.salary.rule.template
        _logger.info('hr.salary.rule.template')
        hsrt = self.env['hr.salary.rule.template'].search([('chart_template_id','=',self.env.user.company_id.chart_template_id.id)])
        for register in hsrt:

            register_contribution = self.env['hr.contribution.register'].search([('name','=',register.name),('company_id','=',self.env.user.company_id.id)])
            parent = self.env['hr.salary.rule'].search([('code','=',register.parent_rule_id.code),('company_id','=',self.env.user.company_id.id)])
            category = self.env['hr.salary.rule.category'].search([('name','=',register.category_id.name),('company_id','=',self.env.user.company_id.id)])
            account_credit = self.env['account.account'].search([('code','=',register.account_credit.code or False),('company_id','=',self.env.user.company_id.id)])
            account_debit = self.env['account.account'].search([('code','=',register.account_debit.code or False),('company_id','=',self.env.user.company_id.id)])
            #account_tax_id = self.env['account.account'].search([('code','=',register.account_tax_id.code or False),('company_id','=',self.env.user.company_id.id)])

            self.env['hr.salary.rule'].create({'parent_rule_id':parent,
                        'code':register.code,
                        'company_id':self.env.user.company_id.id,
                        'sequence':register.sequence,
                        'appears_on_payslip':register.appears_on_payslip,
                        'condition_range':register.condition_range,
                        'amount_fix':register.amount_fix,
                        'note':register.note,
                        'amount_percentage':register.amount_percentage,
                        'condition_range_min':register.condition_range_min,
                        'condition_select':register.condition_select,
                        'amount_percentage_base':register.amount_percentage_base,
                        'register_id':register_contribution.id,
                        'amount_select':register.amount_select,
                        'active':register.active,
                        'condition_range_max':register.condition_range_max,
                        'name':register.name,
                        'condition_python':register.condition_python,
                        'amount_python_compute':register.amount_python_compute,
                        'category_id':category.id,
                        'account_credit':account_credit.id,
                        'account_debit':account_debit.id,
                        #'account_tax_id':account_tax_id.id,
                        })

        #hr.rule.input.template
        _logger.info('hr.rule.input.template')
        hrit = self.env['hr.rule.input.template'].search([('chart_template_id','=',self.env.user.company_id.chart_template_id.id)])
        for register in hrit:
            rule_id = self.env['hr.salary.rule'].search([('code','=',register.input_id.code),('company_id','=',self.env.user.company_id.id)])
            self.env['hr.rule.input'].create({'input_id':rule_id.id,
                        'code':register.code,
                        'name':register.name,
                        'assing_value':register.assing_value})

        #hr.payroll.structure.template
        _logger.info('hr.payroll.structure.template')
        _logger.info(self.env.user.company_id.chart_template_id)
        structure_template = self.env['hr.payroll.structure.template'].search([('chart_template_id','=',self.env.user.company_id.chart_template_id.id)])
        for register in structure_template:
            structure_id = self.env['hr.payroll.structure'].search([('code','=',register.parent_id.code),('company_id','=',self.env.user.company_id.id)])
            
            rule_id = []
            for rules in register.rule_ids:
                rule_id.append(self.env['hr.salary.rule'].search([('code','=',rules.code),('company_id','=',self.env.user.company_id.id)]).id)

            structure = self.env['hr.payroll.structure'].create({'parent_id':structure_id,
                        'code':register.code,
                        'name':register.name,
                        'note':register.note,
                        'note':register.note,
                        'rule_ids':[(6, 0, rule_id)],
                        })
            _logger.info('rule')
            _logger.info(rule_id)
                

        _logger.info('END method apply_hr_template')
        return True
        