# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account(models.Model):
    _inherit = 'account.account'

    parent_id = fields.Many2one('account.account', string='Parent ID')

class contabilidad(models.Model):
    _inherit = 'account.account.template'

    parent_id = fields.Many2one('account.account.template', string='Parent ID')
