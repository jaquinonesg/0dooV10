# -*- coding: utf-8 -*-

from openerp import models, fields, api

class Invoice(models.Model):
	_inherit = 'account.journal'

	dian_resolution = fields.Text('DIAN Resolution')