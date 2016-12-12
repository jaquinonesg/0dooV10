# -*- coding: utf-8 -*-

from openerp import models, fields, api
import xlsxwriter
from datetime import datetime

class account_tax_report_conf(models.Model):
    _name='account.tax.report.conf'

    name = fields.Char(string='Nombre')
    tax_group_ids = fields.Many2many('account.tax.group', string='Grupo de impuestos')
    
class account_tax_report(models.Model):
    _name='account.tax.report'

    name = fields.Char(string='Nombre')
    desde = fields.Date(string='Desde')
    hasta = fields.Date(string='Hasta')
    company_id = fields.Many2one('res.company', string='Compañia')
    user_id = fields.Many2one('res.users', string='Usuario')

class account_tax_report_line(models.Model):
    _name='account.tax.report.line'

    account_id = fields.Many2one('account.account', string='Cuenta contable')
    partner_id = fields.Many2one('res.partner', string='Tercero')
    tax_id = fields.Many2one('account.tax', string='Impuesto')
    tax_group_id = fields.Many2one('account.tax.group', string='Grupo de Impuesto')
    amount = fields.Float(string='Tasa de impuesto')
    base = fields.Float(string='Base imponible',default=0.0)
    impuesto = fields.Float(string='Monto de impuesto',default=0.0)
    encabezado_id = fields.Many2one('account.tax.report', string='Encabezado', ondelete='cascade')
    fecha = fields.Date(string='Fecha de facturación')
    invoice_id = fields.Many2one('account.invoice', string='Factura')

class account_tax_report_wizard(models.TransientModel):
    _name = "account.tax.report.wizard"

    tax_report_id = fields.Many2one('account.tax.report.conf', string='Informe de impuesto',required=True)
    detalle = fields.Boolean(string='Detalle de factura', default=False)
    desde = fields.Date(string='Desde', required=True)
    hasta = fields.Date(string='Hasta', required=True)
  
    @api.multi
    def run(self):
		#Generar
		self.generate()
		ir_model_data = self.env['ir.model.data']
		try:
			compose_tree_id = ir_model_data.get_object_reference( 'bioxsolution_account_tax_report', 'account_tax_report_line_tree_view' )[1]
		except ValueError:
			compose_tree_id = False
		return {
		'name': 'Declaracion de Impuestos',
		'res_model': 'account.tax.report.line',
		'type': 'ir.actions.act_window',
		'view_id': compose_tree_id,
		'view_mode': 'tree',
		'view_type': 'form',
		#'domain': dominio,
		'target': 'current'
			}
            
    @api.multi
    def imprimir(self, data=None):
        self.generate()
        self.env.cr.execute(" SELECT atrl.id FROM account_tax_report at INNER JOIN account_tax_report_line atrl on atrl.encabezado_id = at.id WHERE at.company_id =%s AND at.user_id =%s "%(self.env.user.company_id.id,self.env.user.id))
        datos = self.env.cr.fetchall()
        ids = []
        for res in datos:
            ids.append(res[0])
        print ids
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('bioxsolution_account_tax_report.account_tax_report_pdf')
        print datos
        obj = self.env['account.tax.report.line'].browse(ids)
        print 'encabezado'
        print obj
        docargs = {'doc_ids': ids,'doc_model': report.model,'docs': obj,}
        return report_obj.render('bioxsolution_account_tax_report.account_tax_report_pdf', docargs)

    @api.multi
    def exportar(self):
        #Generar
        self.generate()
        sql = " SELECT id FROM account_tax_report WHERE user_id = %s AND company_id =%s"%(self.env.user.id,self.env.user.company_id.id)
        self.env.cr.execute(" SELECT id FROM account_tax_report WHERE user_id = %s AND company_id =%s"%(self.env.user.id,self.env.user.company_id.id))
        ids = self.env.cr.fetchone()
        actual = str(datetime.now()).replace('-','').replace(':','').replace('.','').replace(' ','')
        data_attach = {
           'name': 'DeclaracionImpuestos_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.'+'xlsx',
           'datas': '.',
           'datas_fname': 'DeclaracionImpuestos_'+self.env.user.company_id.name+self.env.user.name+'_'+actual+'.xlsx',
           'res_model': 'account.tax.report',
           'res_id': ids[0],
        }
        #elimina adjuntos del usuario
        self.env['ir.attachment'].search([('res_model','=','account.tax.report'),('company_id','=',self.env.user.company_id.id),('name','like','%DeclaracionImpuestos%'+self.env.user.name+'%')]).unlink()
        #crea adjunto en blanco
        attachments = self.env['ir.attachment'].create(data_attach)
        url = self.env['ir.config_parameter'].get_param('web.base.url') + '/web/content/%s?download=true'%str(attachments.id)
        path = attachments.store_fname
        self.env['ir.attachment'].search([['store_fname','=',path]]).write({'store_fname':attachments.store_fname})
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(attachments._full_path(path))
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 20)
        bold = workbook.add_format({'bold': True})
        bold.set_align('center')
        worksheet.merge_range('A1:H1', 'DECLARACION DE IMPUESTO: '+self.tax_report_id.name, bold)
        worksheet.write('A3', 'DESDE',bold)
        worksheet.write('B3', self.desde)
        worksheet.write('A4', 'HASTA',bold)
        worksheet.write('B4', self.hasta)
        worksheet.write('A7', 'CUENTA CONTABLE',bold)
        worksheet.write('B7', 'IMPUESTO APLICADO',bold)
        worksheet.write('C7', 'TASA',bold)
        worksheet.write('D7', 'BASE IMPONIBLE',bold)
        worksheet.write('E7', 'MONTO',bold)
        if self.detalle:
			worksheet.write('F7', 'TERCERO',bold)
			worksheet.write('G7', 'REFERENCIA',bold)
			worksheet.write('H7', 'FECHA',bold)
        tax_report_line = self.env['account.tax.report.line'].search([('encabezado_id','=',ids[0])])
        x = 8
        grupos = list(set([ z.tax_group_id for z in tax_report_line]))
        bold2 = workbook.add_format({'bold': True})
        bold2.set_align('left')
        bold3 = workbook.add_format({'bold': True})
        bold3.set_align('right')
        for grupo in grupos:
			base_total, impuesto_total = 0.0,0.0
			pos = 'A'+str(x)+':C'+str(x)
			worksheet.merge_range(pos, grupo.name, bold2)
			for suma in tax_report_line:
				if suma.tax_group_id.id == grupo.id:
					base_total += suma.base
					impuesto_total += suma.impuesto
			worksheet.write('D'+str(x), base_total, bold3)
			worksheet.write('E'+str(x), impuesto_total, bold3)
			x += 1
			for line in tax_report_line:
				if line.tax_group_id.id == grupo.id:
					print line.account_id.name
					worksheet.write('A'+str(x), line.account_id.code + ' - ' + line.account_id.name)
					worksheet.write('B'+str(x), line.tax_id.name)
					worksheet.write('C'+str(x), line.tax_id.amount)
					worksheet.write('D'+str(x), line.base)
					worksheet.write('E'+str(x), line.impuesto)
					if self.detalle:
						partner_name = ''
						if line.partner_id.ref:
							partner_name = line.partner_id.ref
						if line.partner_id.name:
							partner_name = partner_name + '-' + line.partner_id.name
						worksheet.write('F'+str(x), partner_name)
						worksheet.write('G'+str(x), line.invoice_id.number)
						worksheet.write('H'+str(x), line.fecha)
					x += 1
        workbook.close()
        return {'type' : 'ir.actions.act_url','url': str(url),'target': 'self'}

    def generate(self):
		self.env.cr.execute(" DELETE FROM account_tax_report WHERE company_id = %s AND user_id = %s "%(self.env.user.company_id.id, self.env.user.id))
		#INSERT account.tax.report
		tax_report = self.env['account.tax.report'].create({'name':self.tax_report_id.name,'desde':self.desde,'hasta':self.hasta,'company_id':self.env.user.company_id.id,'user_id':self.env.user.id})
		for grupo in self.tax_report_id.tax_group_ids:
			impuesto = self.env['account.tax'].search([('tax_group_id','=',grupo.id)])
			for imp in impuesto:
				#INSERT account.tax.report.line
				if self.detalle:
					sql = " INSERT INTO account_tax_report_line(account_id,tax_id, amount,base,impuesto,encabezado_id,partner_id,fecha,invoice_id, tax_group_id) "\
					" SELECT ait.account_id, ailt.tax_id, at.amount, sum(price_subtotal)as price_subtotal, sum(ait.amount) as amount, %s, "\
					" ail.partner_id, ai.date_invoice, ai.id, %s"\
					" from account_invoice_line_tax ailt "\
					" inner join account_invoice_line  ail on ail.id = ailt.invoice_line_id "\
					" inner join account_invoice ai on ai.id = ail.invoice_id "\
					" inner join account_invoice_tax ait on ait.tax_id = ailt.tax_id and ail.invoice_id = ait.invoice_id "\
					" inner join account_tax at on at.id = ailt.tax_id "\
					" WHERE ai.state NOT IN ('draft','cancel') AND ai.date_invoice BETWEEN '%s' AND '%s' AND at.id = %s "\
					" GROUP BY ait.account_id, ail.partner_id,ailt.tax_id, at.amount, ai.date_invoice, ai.id "%(tax_report.id, grupo.id, self.desde, self.hasta,imp.id)
				else:
					sql = " INSERT INTO account_tax_report_line(account_id, tax_id, amount, base, impuesto, encabezado_id, tax_group_id) "\
					" SELECT ait.account_id, at.id as tax_id, at.amount, sum(price_subtotal)as price_subtotal, sum(ait.amount) as amount, "\
					" %s, %s from account_invoice_line_tax ailt "\
					" inner join account_invoice_line  ail on ail.id = ailt.invoice_line_id "\
					" inner join account_invoice ai on ai.id = ail.invoice_id "\
					" inner join account_invoice_tax ait on ait.tax_id = ailt.tax_id and ail.invoice_id = ait.invoice_id "\
					" inner join account_tax at on at.id = ailt.tax_id "\
					" WHERE ai.state NOT IN ('draft','cancel') AND ai.date_invoice BETWEEN '%s' AND '%s' AND at.id = %s "\
					" GROUP BY ait.account_id, at.id, at.amount "%(tax_report.id, grupo.id, self.desde, self.hasta,imp.id)
				self.env.cr.execute(sql)
		return True
