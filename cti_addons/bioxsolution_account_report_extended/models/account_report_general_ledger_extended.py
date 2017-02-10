# -*- coding: utf-8 -*-

import time
import xlsxwriter
from datetime import datetime
from openerp import api, models, _


class AccountReportGeneralLedgerExtended(models.TransientModel):
    _inherit = 'account.report.general.ledger'
    
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
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
        accounts = self.env['account.account'].search([])
        account_res = self.env['report.account.report_generalledger'].with_context(used_context)._get_account_move_entry(accounts, init_balance, sortby, display_account)
        return self.generate(account_res,data)

    @api.multi
    def generate(self,account_res,data):
        actual = str(datetime.now()).replace('-','').replace(':','').replace('.','').replace(' ','')
        data_attach = {
           'name': 'Mayor_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.'+'xlsx',
           'datas': '.',
           'datas_fname': 'Mayor_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.xlsx',
           'res_model': 'account.report.general.ledger',
           'res_id': self.id,
        }
        #elimina adjuntos del usuario
        self.env['ir.attachment'].search([('res_model','=','account.report.general.ledger'),('company_id','=',self.env.user.company_id.id),('name','like','%Mayor%'+self.env.user.name+'%')]).unlink()
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
        journal_ids = self.env['account.journal'].browse(data['form'].get('journal_ids'))
        journal_ids = ', '.join([ x.code or '' for x in journal_ids ])
        worksheet.merge_range('A1:I1', self.company_id.name + _(': General Ledger'), bold)
        worksheet.merge_range('A3:C3', _('Journal:'),bold)
        worksheet.merge_range('A4:C4', journal_ids)
        worksheet.merge_range('D3:F3', _('Show Account:'),bold)
        worksheet.merge_range('D4:F4', data['form'].get('display_account'))
        worksheet.merge_range('G3:H3', _('Target Moves:'),bold)
        worksheet.merge_range('G4:H4', data['form'].get('target_move'))
        worksheet.merge_range('A5:C5', _('Order by:'),bold)
        worksheet.merge_range('A6:C6', data['form'].get('sortby'))
        worksheet.write('D5', _('Date from:'),bold)
        worksheet.write('E5', data['form']['used_context'].get('date_from'))
        worksheet.write('D6', _('Date to:'),bold)
        worksheet.write('E6', data['form']['used_context'].get('date_to'))
        #Titles
        worksheet.write('A7', _('Date'),bold)
        worksheet.write('B7', _('Journal'),bold)
        worksheet.write('C7', _('Partner'),bold)
        worksheet.write('D7', _('Ref'),bold)
        worksheet.write('E7', _('Move'),bold)
        worksheet.write('F7', _('Label'),bold)
        worksheet.write('G7', _('Debit'),bold)
        worksheet.write('H7', _('Credit'),bold)
        worksheet.write('I7', _('Balance'),bold)
        c = 8
        bold2 = workbook.add_format({'bold': False})
        bold2.set_font_color('blue')
        for lines in account_res:
            worksheet.merge_range('A'+str(c)+':F'+str(c), lines.get('code')+' - '+lines.get('name'),bold2)
            worksheet.write('G'+str(c), lines.get('debit'),bold2)
            worksheet.write('H'+str(c), lines.get('credit'),bold2)
            worksheet.write('I'+str(c), lines.get('balance'),bold2)
            c += 1
            for move in lines.get('move_lines'):
                worksheet.write('A'+str(c), move.get('ldate'))
                worksheet.write('B'+str(c), move.get('lcode'))
                worksheet.write('C'+str(c), move.get('partner_name'))
                worksheet.write('D'+str(c), move.get('lref'))
                worksheet.write('E'+str(c), move.get('move_name'))
                worksheet.write('F'+str(c), move.get('lname'))
                worksheet.write('G'+str(c), move.get('debit'))
                worksheet.write('H'+str(c), move.get('credit'))
                worksheet.write('I'+str(c), move.get('balance'))
                
                c += 1
        workbook.close()
        return {'type' : 'ir.actions.act_url','url': str(url),'target': 'self'}
