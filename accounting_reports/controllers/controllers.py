# -*- coding: utf-8 -*-
from openerp import http

# class L10nCoAccountReports(http.Controller):
#     @http.route('/l10n_co_account_reports/l10n_co_account_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_co_account_reports/l10n_co_account_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_co_account_reports.listing', {
#             'root': '/l10n_co_account_reports/l10n_co_account_reports',
#             'objects': http.request.env['l10n_co_account_reports.l10n_co_account_reports'].search([]),
#         })

#     @http.route('/l10n_co_account_reports/l10n_co_account_reports/objects/<model("l10n_co_account_reports.l10n_co_account_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_co_account_reports.object', {
#             'object': obj
#         })