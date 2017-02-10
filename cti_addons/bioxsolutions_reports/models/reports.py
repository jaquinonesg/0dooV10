# -*- coding: utf-8 -*-
import openerp
import xlsxwriter
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp.addons.base.res import res_request
from datetime import datetime
import subprocess
import os

class report_params(models.Model):
    _name = 'bx.reports.params'

    @api.multi
    def _list_value_model(self):
        self.env.cr.execute("SELECT model, name FROM ir_model ORDER BY name")
        return self.env.cr.fetchall()

    code = fields.Char(string='Code', required=True)
    report_id = fields.Many2one('bx.reports', string='Report', required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    type = fields.Selection([('C', 'Char'), ('D', 'Date'), ('N', 'Numeric'), ('B', 'Boolean'), ('S', 'Selection')], string="Type", required=True)
    value = fields.Char('Value Char')
    dates = fields.Date('Value date')
    numerics = fields.Float('Value numeric')
    logic= fields.Boolean('Value logic')

class reports(models.Model):
    _name = 'bx.reports'

    name = fields.Char(string='Name', required=True)
    field_sql = fields.Char(string='Fields (Order)', required=True)
    titles_sql = fields.Char(string='Titles', required=True)
    sql = fields.Text(string='SQL',required=True)
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], 'Estado', default='draft')
    send_mail = fields.Selection([('PQ', 'Partner Manual'), ('PG', 'Partner Generate')], 'Send mail', required=True)
    partner_ids = fields.Many2many('res.partner',string='Partner')
    params_ids = fields.One2many('bx.reports.params', 'report_id', string='Parameters', copy=True)
    template_id = fields.Many2one('mail.template', string='Template', required=True)

    @api.one
    def draft(self):
        self.write({'state': 'draft'})
        self.env['bx.reports.execute'].search([('report_id','=',self.id)]).unlink()
        return True

    @api.one
    def validated(self):
        try:
            if 'insert' in self.sql.lower():
                raise UserError("The query should not have insert")
            elif 'update' in self.sql.lower():
                raise UserError("The query should not have update")
            elif 'delete' in self.sql.lower():
                raise UserError("The query should not have update")
            #else:
                #for params in self.params_ids:
                #    print params.code
                #self.env.cr.execute(self.sql)
        except:
            raise UserError("Please check the SQL query")
        id = self.env['bx.reports.execute'].create({'send_mail':self.send_mail,'name':self.name,'sql':self.sql,'titles_sql':self.titles_sql,'field_sql':self.field_sql,'report_id':self.id})
        for params in self.params_ids:
            self.env['bx.reports.execute.params'].create({'name':params.name, 'code':params.code, 'report_id':id.id, 'type':params.type})
        self.write({'state': 'validated'})
        return True

class reports_inherit(models.Model):
    _name = 'bx.reports.execute'
    _inherit = 'bx.reports'

    params_ids = fields.One2many('bx.reports.execute.params', 'report_id', string='Parameters')
    report_id = fields.Many2one('bx.reports', string='Report', required=True, ondelete='cascade')
    format = fields.Selection([('pdf','PDF'),('xlsx','XLSX')],string="Format")

    @api.multi
    def generate(self):
        if self._context is None:
            self._context = {}
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference('bioxsolutions_reports', 'report_export_wizard_view')[
                1]
        except ValueError:
            compose_form_id = False
        return {
            'name': _(self.name),
            'res_model': 'bx.reports.execute',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'view_id': compose_form_id,
            'nodestroy': True,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'params_ids': [x.id for x in self.params_ids]},
        }
    @api.multi
    def export(self):
        data = self.execute()
        if self.format =='xlsx':           
            return self.xlsx(data)
        elif self.format =='pdf':
            return self.pdf(data)

    @api.one
    def execute(self):
        sql = self.sql
        try:
            for params in self.params_ids:
                if params.type == 'S':
                    sql = sql.replace(str(params.code),str(params.selection.id))
                if params.type == 'C':
                    sql = sql.replace(params.code, params.value)
                if params.type == 'B':
                    sql = sql.replace(params.code, params.logic)
                if params.type == 'N':
                    sql = sql.replace(params.code, params.numerics)
                if params.type == 'D':
                    sql = sql.replace(params.code, params.dates)
            self.env.cr.execute(sql)
        except:
            raise UserError("Please check the SQL query")
        return self.env.cr.dictfetchall()

    @api.multi
    def pdf(self, data):
        actual = str(datetime.now()).replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
        data_attach = {
            'name': self.report_id.name+'_' + self.env.user.company_id.name + self.env.user.name + '_' + actual + '.xlsx',
            'datas': '.',
            'datas_fname': self.report_id.name+'_' + self.env.user.company_id.name + self.env.user.name + '_' + actual + '.xlsx',
            'res_model': 'bx.reports.execute',
            'res_id': self.id,
        }
        # elimina adjuntos del usuario
        self.env['ir.attachment'].search(
            [('res_model', '=', 'bx.reports.execute'), ('company_id', '=', self.env.user.company_id.id),
             ('name', 'like', '%'+self.report_id.name+'%' + self.env.user.name + '%')]).unlink()
        # crea adjunto en blanco
        attachments = self.env['ir.attachment'].create(data_attach)
        url = self.env['ir.config_parameter'].get_param('web.base.url') + '/web/content/%s?download=true' % str(
            attachments.id)
        path = attachments.store_fname
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(attachments._full_path(path))
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 20)
        bold = workbook.add_format({'bold': True})
        blue = workbook.add_format({'color': 'blue'})
        bold.set_align('center')
        worksheet.merge_range('A1:F1', self.env.user.company_id.name + _(': '+self.report_id.name.upper()), bold)
        x = 3
        for params in self.params_ids:
            worksheet.write('A'+str(x), _(params.name+':'), bold)
            if params.type == 'S':
                worksheet.write('B' + str(x), _(params.selection.name or params.selection.code + ':'))
            if params.type == 'C':
                worksheet.write('B' + str(x), _(params.value + ':'))
            if params.type == 'B':
                worksheet.write('B' + str(x), _(params.logic + ':'))
            if params.type == 'N':
                worksheet.write('B' + str(x), _(params.numerics + ':'))
            if params.type == 'D':
                worksheet.write('B' + str(x), _(params.dates + ':'))

            x += 1
        abc = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
               'V', 'W', 'X', 'Y', 'Z']
        num = [x for x in range(0, 101)]
        resultado = zip(abc, num)
        title = self.titles_sql.split(',')
        position = ''
        # Agrega titulos
        for i, l in enumerate(title):
            for pos in resultado:
                if i == pos[1]:
                    position = pos[0]
                    break
            titles = position
            worksheet.write(position + str(8), l, bold)
        x = 9
        for line in data:
            for i, l in enumerate(self.field_sql.split(',')):
                for pos in resultado:
                    if i == pos[1]:
                        position = pos[0]
                        break
                titles = position
                if line:
                    worksheet.write(position + str(x), line[0][str(l)], bold)
            x += 1
        #bold2 = workbook.add_format({'bold': False})
        #bold2.set_font_color('blue')
        workbook.close()
        try:
            subprocess.check_call(['/usr/bin/python3', '/usr/bin/unoconv', attachments._full_path(path)])
            os.system("mv "+attachments._full_path(path)+'.pdf'+" "+attachments._full_path(path))
        except subprocess.CalledProcessError as e:
            print('CalledProcessError', e)
        attachments.datas_fname = attachments.datas_fname.replace('.xlsx','.pdf')
        attachments.name = attachments.name.replace('.xlsx','.pdf')
        return {'type': 'ir.actions.act_url', 'url': str(url), 'target': 'self'}

    @api.multi
    def xlsx(self, data):
        actual = str(datetime.now()).replace('-', '').replace(':', '').replace('.', '').replace(' ', '')
        data_attach = {
            'name': self.report_id.name+'_' + self.env.user.company_id.name + self.env.user.name + '_' + actual + '.xlsx',
            'datas': '.',
            'datas_fname': self.report_id.name+'_' + self.env.user.company_id.name + self.env.user.name + '_' + actual + '.xlsx',
            'res_model': 'bx.reports.execute',
            'res_id': self.id,
        }
        # elimina adjuntos del usuario
        self.env['ir.attachment'].search(
            [('res_model', '=', 'bx.reports.execute'), ('company_id', '=', self.env.user.company_id.id),
             ('name', 'like', '%'+self.report_id.name+'%' + self.env.user.name + '%')]).unlink()
        # crea adjunto en blanco
        attachments = self.env['ir.attachment'].create(data_attach)
        url = self.env['ir.config_parameter'].get_param('web.base.url') + '/web/content/%s?download=true' % str(
            attachments.id)
        path = attachments.store_fname
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(attachments._full_path(path))
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 20)
        bold = workbook.add_format({'bold': True})
        blue = workbook.add_format({'color': 'blue'})
        bold.set_align('center')
        worksheet.merge_range('A1:F1', self.env.user.company_id.name + _(': '+self.report_id.name.upper()), bold)
        x = 3
        for params in self.params_ids:
            worksheet.write('A'+str(x), _(params.name+':'), bold)
            if params.type == 'S':
                worksheet.write('B' + str(x), _(params.selection.name or params.selection.code + ':'))
            if params.type == 'C':
                worksheet.write('B' + str(x), _(params.value + ':'))
            if params.type == 'B':
                worksheet.write('B' + str(x), _(params.logic + ':'))
            if params.type == 'N':
                worksheet.write('B' + str(x), _(params.numerics + ':'))
            if params.type == 'D':
                worksheet.write('B' + str(x), _(params.dates + ':'))

            x += 1
        abc = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
               'V', 'W', 'X', 'Y', 'Z']
        num = [x for x in range(0, 101)]
        resultado = zip(abc, num)
        title = self.titles_sql.split(',')
        position = ''
        # Agrega titulos
        for i, l in enumerate(title):
            for pos in resultado:
                if i == pos[1]:
                    position = pos[0]
                    break
            titles = position
            worksheet.write(position + str(8), l, bold)
        x = 9
        for line in data:
            for i, l in enumerate(self.field_sql.split(',')):
                for pos in resultado:
                    if i == pos[1]:
                        position = pos[0]
                        break
                titles = position
                if line:
                    worksheet.write(position + str(x), line[0][str(l)], bold)
            x += 1
        #bold2 = workbook.add_format({'bold': False})
        #bold2.set_font_color('blue')
        workbook.close()
        return {'type': 'ir.actions.act_url', 'url': str(url), 'target': 'self'}

    @api.multi
    def sendmail(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        #template = self.env.ref(self.template, False)
        template = self.template_id
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        partner = []
        for x in self.partner_ids:
            partner.append(x.id)

        ctx = dict(
            default_model='bx.reports.execute',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            default_partner_ids=partner,
            #mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

class report_execute_params(models.Model):
    _name = 'bx.reports.execute.params'
    _inherit = 'bx.reports.params'

    def referencable_models(self):
        obj = self.env['ir.model']
        ids = obj.search([])
        res = ids.read(['model', 'name'])
        return [(r['model'], r['name']) for r in res]

    report_id = fields.Many2one('bx.reports.execute', string='Report execute', required=True, ondelete='cascade')
    selection = fields.Reference(selection='referencable_models', string='Selection')