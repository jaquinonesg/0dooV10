# -*- coding: utf-8 -*-
from openerp import http

# class AccountPdfReports(http.Controller):
#     @http.route('/account_pdf_reports/account_pdf_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_pdf_reports/account_pdf_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_pdf_reports.listing', {
#             'root': '/account_pdf_reports/account_pdf_reports',
#             'objects': http.request.env['account_pdf_reports.account_pdf_reports'].search([]),
#         })

#     @http.route('/account_pdf_reports/account_pdf_reports/objects/<model("account_pdf_reports.account_pdf_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_pdf_reports.object', {
#             'object': obj
#         })