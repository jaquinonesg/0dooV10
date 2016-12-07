# -*- coding: utf-8 -*-
from odoo import http

# class L10nCoHr(http.Controller):
#     @http.route('/l10n_co_hr/l10n_co_hr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_co_hr/l10n_co_hr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_co_hr.listing', {
#             'root': '/l10n_co_hr/l10n_co_hr',
#             'objects': http.request.env['l10n_co_hr.l10n_co_hr'].search([]),
#         })

#     @http.route('/l10n_co_hr/l10n_co_hr/objects/<model("l10n_co_hr.l10n_co_hr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_co_hr.object', {
#             'object': obj
#         })