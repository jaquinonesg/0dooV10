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


{
    'name': 'Employee Colombia',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
Add all information on the employee Colombia.
=============================================================

    * Social Security
    * Social Security type

You can assign several contracts per employee.
    """,
    'author': '3RP SA',
    'website': 'http://www.3rp.co',
    'images': ['images/hr_contract.jpeg'],
    'depends': [
            #'hr_evaluation',
            'hr_payroll_account',
    ],
    'data': [
        'hr_employee_view.xml',
        'hr_payroll_account_view.xml',
        # Cancel play_slip
        'hr_payslip_view.xml',
        
        #'security/ir.model.access.csv',
        #'security/hr_security.xml',

        # Localización Colombia
        'hr_holidays_data.xml',
        'data/resource_calendar.xml',     
        'data/hr_contribution_register.xml',   

        'data/hr_salary_rule_category.xml',     
        'data/hr_salary_rule_template_comercial_admin.xml',     
        'data/hr_salary_rule_template_comercial_ventas.xml',     
        'data/hr_salary_rule_template_comercial_produccion.xml',     
        'data/hr_salary_rule_template_comercial_integral.xml',     
        'data/hr_payroll_structure_template_comercial.xml',   
        
        'data/hr_salary_rule_template_solidario_admin.xml',     
        'data/hr_salary_rule_template_solidario_ventas.xml',     
        'data/hr_salary_rule_template_solidario_produccion.xml',     
        'data/hr_salary_rule_template_solidario_integral.xml',     
        'data/hr_payroll_structure_template_solidario.xml',     

    ],
    'demo': [],
    'css': ['static/src/css/partner_rules.css'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
