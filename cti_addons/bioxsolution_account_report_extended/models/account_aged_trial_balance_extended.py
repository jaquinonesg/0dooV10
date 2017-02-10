# -*- coding: utf-8 -*-

import time
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import datetime
from openerp import api, models
from openerp import _

class AccountAgedTrialBalanceExtended(models.TransientModel):
    _inherit = 'account.aged.trial.balance'
    
    @api.multi
    def render_xlsx(self, data):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move','result_selection'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        self.total_account = []
        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable','receivable']
            
        aged = self.env['report.account.report_agedpartnerbalance']
        aged.total_account=[]
        res = {}
        data = self.pre_print_report(data)
        data['form'].update(self.read(['period_length'])[0])
        period_length = data['form']['period_length']
        if period_length<=0:
            raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")

        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data['form'].update(res)
        without_partner_movelines = aged._get_move_lines_with_out_partner(data['form'], account_type, date_from, target_move)
        tot_list = self.total_account
        partner_movelines = aged._get_partner_move_lines(data['form'], account_type, date_from, target_move)
        return self.generate(partner_movelines,data)

    @api.multi
    def generate(self,account_res,data):
        actual = str(datetime.now()).replace('-','').replace(':','').replace('.','').replace(' ','')
        data_attach = {
           'name': 'AgedBalance'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.'+'xlsx',
           'datas': '.',
           'datas_fname': 'Mayor_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.xlsx',
           'res_model': 'account.report.general.ledger',
           'res_id': self.id,
        }
        #elimina adjuntos del usuario
        self.env['ir.attachment'].search([('res_model','=','account.report.general.ledger'),('company_id','=',self.env.user.company_id.id),('name','like','%AgedBalance%'+self.env.user.name+'%')]).unlink()
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
        print 'Init Date:'
        print _('Init Date:')
        journal_ids = self.env['account.journal'].browse(data['form'].get('journal_ids'))
        journal_ids = ', '.join([ x.code or '' for x in journal_ids ])
        worksheet.merge_range('A1:H1', self.company_id.name + _(': AgedBalance'), bold)
        worksheet.merge_range('A3:C3', _('Init Date:'),bold)
        worksheet.merge_range('A4:C4', data['form']['used_context'].get('date_from'))
        worksheet.merge_range('D3:F3', _('Long Period:'),bold)
        worksheet.merge_range('D4:F4', data['form'].get('period_length'))
        worksheet.merge_range('G3:H3', _('Accounts:'),bold)
        worksheet.merge_range('G4:H4', data['form'].get('result_selection'))
        worksheet.merge_range('A5:C5', _('Target Moves:'),bold)
        worksheet.merge_range('A6:C6', data['form'].get('target_move'))
        #Titles
        worksheet.write('A7', _('Partner'),bold)
        worksheet.write('B7', _('Not overcome'),bold)
        worksheet.write('C7', '0-30',bold)
        worksheet.write('D7', '30-60',bold)
        worksheet.write('E7', '60-90',bold)
        worksheet.write('F7', '90-120',bold)
        worksheet.write('G7', '+120',bold)
        worksheet.write('H7', _('Amount'),bold)
        c = 8
        bold2 = workbook.add_format({'bold': False})
        bold2.set_font_color('blue')
        for lines in account_res:
            worksheet.write('A'+str(c), lines.get('name'))
            worksheet.write('B'+str(c), lines.get('direction'))
            worksheet.write('C'+str(c), lines.get('4'))
            worksheet.write('D'+str(c), lines.get('3'))
            worksheet.write('E'+str(c), lines.get('2'))
            worksheet.write('F'+str(c), lines.get('1'))
            worksheet.write('G'+str(c), lines.get('0'))
            worksheet.write('H'+str(c), lines.get('total'))
            c +=1
        workbook.close()
        return {'type' : 'ir.actions.act_url','url': str(url),'target': 'self'}
