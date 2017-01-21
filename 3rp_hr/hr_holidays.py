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
from datetime import date, datetime, timedelta
from openerp import models, fields
from openerp.tools import config
from openerp.tools.translate import _

import logging

_logger = logging.getLogger('3RP')

class hr_holidays_status(models.Model):
    
    _inherit = "hr.holidays.status"
    _description = "Leave Type"
    
    code = fields.Char('Code', size=64, required=True, readonly=False)
