# -*- coding: utf-8 -*-

import time
import xlsxwriter
from datetime import datetime
from openerp import api, models, _


class ReportTrialBalance(models.AbstractModel):
    _name = 'report.account.report_trialbalance'

    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters_si = filters.replace('(("account_move_line"."date" <= %s)  AND  ("account_move_line"."date" >= %s))  AND','("account_move_line"."date" < \'%s\')  AND'%str(where_params[1]))
        filters_si = filters.replace('("account_move_line"."date" <= %s)  AND  ("account_move_line"."date" >= %s)','("account_move_line"."date" < \'%s\') '%str(where_params[1]))
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT parent.id, sum(si) as si, sum(debit) as debit, sum(credit) as credit, sum(si+debit-credit) as balance "+\
                   " FROM (SELECT account_id AS id, 0 as si, SUM(debit) AS debit, SUM(credit) AS credit " +\
                   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id "+\
                   " UNION "+\
                   " SELECT account_id, SUM(debit-credit) as si, 0 as debit, 0 as credit " +\
                   " FROM "+tables+ " WHERE account_id IN %s "+filters_si+" GROUP BY account_id) as tabla"+\
                   " INNER JOIN account_account aa on aa.id = tabla.id "+\
                   " INNER JOIN account_account parent on aa.code like parent.code ||%s or parent.code ='0'"+\
                   " GROUP BY parent.id " +\
                   " ORDER BY parent.code::character varying asc")
        print 'len(where_params)'
        print len(where_params)
        if len(where_params)>2:
            params = (tuple(accounts.ids),) + tuple(where_params) + (tuple(accounts.ids),) + (where_params[2],) + ('%',)    
        else:
            params = (tuple(accounts.ids),) + tuple(where_params) + (tuple(accounts.ids),) + ('%',)
        print '----------------------------'
        print request
        print '----------------------------'
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row
        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['si','credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            res['type'] = account.user_type_id.type
            if account.id in account_result.keys():
                res['si'] = account_result[account.id].get('si')
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = abs(account_result[account.id].get('balance')) if currency.is_zero(account_result[account.id].get('balance')) else account_result[account.id].get('balance')
                
            if display_account == 'all':
                account_res.append(res)
            if display_account in ['movement', 'not_zero'] and (not currency.is_zero(res['balance']) or res['code'] == '0'):
                account_res.append(res)
        return account_res

    @api.multi
    def render_html(self, data):
        if not self:
            self.model = 'report.account.report_trialbalance'
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': account_res,
        }
        return self.env['report'].render('bioxsolution_account_report_extended.report_trialbalance_extended', docargs)

class ReportTrialBalanceExtendedXlsx(models.TransientModel):
    _inherit = 'account.balance.report'

    @api.multi
    def render_xlsx(self, data):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        
        data = self.pre_print_report(data)
        display_account = data['form'].get('display_account')
        accounts = self.env['account.account'].search([])
        account_res = self.env['report.account.report_trialbalance'].with_context(used_context)._get_accounts(accounts, display_account)
        return self.generate(account_res,data)
        
    @api.multi
    def generate(self,account_res,data):
        actual = str(datetime.now()).replace('-','').replace(':','').replace('.','').replace(' ','')
        data_attach = {
           'name': 'TrialBalance_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.'+'xlsx',
           'datas': '.',
           'datas_fname': 'TrialBalance_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.xlsx',
           'res_model': 'account.balance.report',
           'res_id': self.id,
        }
        #elimina adjuntos del usuario
        self.env['ir.attachment'].search([('res_model','=','account.balance.report'),('company_id','=',self.env.user.company_id.id),('name','like','%TrialBalance%'+self.env.user.name+'%')]).unlink()
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
        worksheet.merge_range('A1:F1', self.company_id.name + _(': Trial Balance'), bold)
        worksheet.write('A3', _('Display Account:'),bold)
        worksheet.write('A4', data['form'].get('display_account'))
        worksheet.write('C3', _('Date From'),bold)
        worksheet.write('D3', data['form']['used_context'].get('date_from'))
        worksheet.write('C4', _('Date To'),bold)
        worksheet.write('D4', data['form']['used_context'].get('date_to'))
        worksheet.write('E3', _('Target Moves:'),bold)
        worksheet.write('E4', data['form'].get('target_move'))
        worksheet.write('A7', _('Code'),bold)
        worksheet.write('B7', _('Account'),bold)
        worksheet.write('C7', _('Init Balance'),bold)
        worksheet.write('D7', _('Debit'),bold)
        worksheet.write('E7', _('Credit'),bold)
        worksheet.write('F7', _('Balance'),bold)
        c = 8
        bold2 = workbook.add_format({'bold': False})
        bold2.set_font_color('blue')
        for lines in account_res:
            #blue
            if lines.get('type') == 'view':
                worksheet.write('A'+str(c), lines.get('code'),bold2)
                worksheet.write('B'+str(c), lines.get('name'),bold2)
                worksheet.write('C'+str(c), lines.get('si'),bold2)
                worksheet.write('D'+str(c), lines.get('debit'),bold2)
                worksheet.write('E'+str(c), lines.get('credit'),bold2)
                worksheet.write('F'+str(c), lines.get('balance'),bold2)
            else:
                worksheet.write('A'+str(c), lines.get('code'))
                worksheet.write('B'+str(c), lines.get('name'))
                worksheet.write('C'+str(c), lines.get('si'))
                worksheet.write('D'+str(c), lines.get('debit'))
                worksheet.write('E'+str(c), lines.get('credit'))
                worksheet.write('F'+str(c), lines.get('balance'))
            c += 1
        workbook.close()
        return {'type' : 'ir.actions.act_url','url': str(url),'target': 'self'}
