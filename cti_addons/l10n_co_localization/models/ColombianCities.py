# -*- coding: utf-8 -*-

from openerp import models, fields, api, _

class CountryStateCity(models.Model):
    _name = 'res.country.state.city'
    _description = 'Cities of states'

    state_id = fields.Many2one('res.country.state', string='State',required=True)
    name = fields.Char(required=True)
    code = fields.Char(string='City code', required=True)

class Partner(models.Model):
    _inherit = 'res.partner'

    city_id = fields.Many2one('res.country.state.city', string = 'City', ondelete='restrict')

    @api.multi
    def onchange_city(self, city_id):
        if city_id:
            city = self.env['res.country.state.city'].browse(city_id)
            return {'value': {'state_id': city.state_id.id,
                              'city': city.name}}
        return {'value': {}}

class Bank(models.Model):
    _inherit = 'res.bank'

    city_id = fields.Many2one('res.country.state.city', string = 'City', ondelete='restrict')

    @api.multi
    def onchange_city(self, city_id):
        if city_id:
            city = self.env['res.country.state.city'].browse(city_id)
            return {'value': {'state': city.state_id.id,
                              'city': city.name}}
        return {'value': {}}

class Company(models.Model):
    _inherit = 'res.company'

    city_id = fields.Many2one('res.country.state.city', string = 'City', ondelete='restrict')

    @api.multi
    def onchange_city(self, city_id):
        if city_id:
            city = self.env['res.country.state.city'].browse(city_id)
            return {'value': {'state_id': city.state_id.id,
                              'city': city.name}}
        return {'value': {}}
