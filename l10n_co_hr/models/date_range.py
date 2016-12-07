# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DateRange(models.Model):
    _inherit = "date.range"

    attributes_ids = fields.One2many('date.range.attribute', 'range_id', string='Range Attributes')