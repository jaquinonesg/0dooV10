# -*- coding: utf-8 -*-

import time
from openerp import api, models, _
from datetime import datetime
import xlsxwriter

class ReportFinancialExtended(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def _compute_account_balance(self, accounts):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
            'si' : '0 as si',
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            filtersi = " AND ".join(wheres)
            filtersi = filtersi.replace('(("account_move_line"."date" <= %s)  AND  ("account_move_line"."date" >= %s)) ','("account_move_line"."date" < %s)')
            wh = []
            if len(where_params)>=2:
                if '-' in str(where_params[1]):
                    wh.append(where_params[1])
                    for x in where_params[2:]:
                        wh.append(str(x))
                elif '-' in str(where_params[0]):
                    wh.append(where_params[0])
                    for x in where_params[1:]:
                        wh.append(str(x))
            request = " SELECT DISTINCT id, sum(si) as si, sum(balance) as balance, sum(debit) as debit, sum(credit) as credit "\
                       " FROM (SELECT account_id as id, " + ', '.join(mapping.values()) + \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " \
                            + filters + \
                       " GROUP BY account_id " \
                       " UNION " \
                       " SELECT account_id as id, 0, SUM(COALESCE(debit-credit,0)) as si, 0,0 " \
                       " FROM " + tables + \
                       " WHERE account_id IN %s " + filtersi + \
                       " GROUP BY account_id) as tabla GROUP BY id "
            params = (tuple(accounts._ids),) + tuple(where_params) + (tuple(accounts._ids),) + tuple(wh) #+ ('%',)  
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['si','credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def get_account_lines(self, data):
        lines = []
        if not data.get('account_report_id',False):
            data['account_report_id'] = data['form']['account_report_id']
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * report.sign,
                'si': res[report.id]['si'] * report.sign,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False, #used to underline the financial report balances
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'si': value['si'] * report.sign,
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']) or not account.company_id.currency_id.is_zero(vals['si']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        report_lines = self.get_account_lines(data.get('form'))
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_account_lines': report_lines,
        }
        return self.env['report'].render('bioxsolution_account_report_extended.report_financial', docargs)

class AccountingReportXlsx(models.TransientModel):
    _inherit = 'accounting.report'
    
    @api.multi
    def render_xlsx(self, data):
        
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move','account_report_id','display_account'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        data = self._print_report(data)
        data = data['data']
        display_account = data['form'].get('display_account')
        accounts = self.env['account.account'].search([])
        account_res = self.env['report.account.report_financial'].with_context(used_context).get_account_lines(data.get('form'))
        return self.generate(account_res,data)
        
    @api.multi
    def generate(self,account_res,data):
        print data
        name = data['form']['account_report_id'][1]
        actual = str(datetime.now()).replace('-','').replace(':','').replace('.','').replace(' ','')
        data_attach = {
           'name': name+'_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.'+'xlsx',
           'datas': '.',
           'datas_fname': name+'_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.xlsx',
           'res_model': 'accounting.report',
           'res_id': self.id,
        }
        #elimina adjuntos del usuario
        self.env['ir.attachment'].search([('res_model','=','accounting.report'),('company_id','=',self.env.user.company_id.id),('name','like','%TrialBalance%'+self.env.user.name+'%')]).unlink()
        #crea adjunto en blanco
        attachments = self.env['ir.attachment'].create(data_attach)
        url = self.env['ir.config_parameter'].get_param('web.base.url') + '/web/content/%s?download=true'%str(attachments.id)
        path = attachments.store_fname
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(attachments._full_path(path))
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 20)
        bold = workbook.add_format({'bold': True})
        blue = workbook.add_format({'color': 'blue'})
        bold.set_align('center')
        worksheet.merge_range('A1:F1', self.company_id.name + ':'+ name, bold)
        worksheet.write('A3', _('Display Account:'),bold)
        worksheet.write('A4', data['form'].get('display_account'))
        worksheet.write('C3', _('Date From'),bold)
        worksheet.write('D3', data['form']['used_context'].get('date_from'))
        worksheet.write('C4', _('Date To'),bold)
        worksheet.write('D4', data['form']['used_context'].get('date_to'))
        worksheet.write('E3', _('Target Moves:'),bold)
        worksheet.write('E4', data['form'].get('target_move'))
        worksheet.write('A7', _('Account'),bold)
        worksheet.write('B7', _('Init Balance'),bold)
        worksheet.write('C7', _('Debit'),bold)
        worksheet.write('D7', _('Credit'),bold)
        worksheet.write('E7', _('Balance'),bold)
        c = 8
        bold2 = workbook.add_format({'bold': False})
        bold2.set_font_color('blue')
        for lines in account_res:
            #blue
            if lines.get('level') != 4:
                worksheet.write('A'+str(c), lines.get('name'),bold2)
                worksheet.write('B'+str(c), lines.get('si'),bold2)
                worksheet.write('C'+str(c), lines.get('debit'),bold2)
                worksheet.write('D'+str(c), lines.get('credit'),bold2)
                worksheet.write('E'+str(c), lines.get('balance'),bold2)
            else:
                worksheet.write('A'+str(c), lines.get('name'))
                worksheet.write('B'+str(c), lines.get('si'))
                worksheet.write('C'+str(c), lines.get('debit'))
                worksheet.write('D'+str(c), lines.get('credit'))
                worksheet.write('E'+str(c), lines.get('balance'))
            c += 1
        workbook.close()
        return {'type' : 'ir.actions.act_url','url': str(url),'target': 'self'}
