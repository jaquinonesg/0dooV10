# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DateRangeAttribute(models.Model):
    _name = 'date.range.attribute'
    
    @api.model
    def _default_company(self):
        return self.env['res.company']._company_default_get('fiscalyear.attribute')

    company_id = fields.Many2one( comodel_name='res.company', string='Company', select=1, default=_default_company)
    name = fields.Char(string='Description', required=True,
    	help='The name that will be used on the attribute')
    value = fields.Char(string='Value', required=True,
    	help="The attribute's value",)
    range_id = fields.Many2one('date.range', string='Date Range', ondelete='cascade')