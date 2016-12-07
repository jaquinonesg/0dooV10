# -*- encoding: utf-8 -*-
# OpenERP, Open Source Management Solution
# Copyright 2016 Christian Camilo Camargo,
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""
 Conventions:
    o_var: var type object
    s_var: var type string (char)
    i_var: var type integer
    f_var: var type float
Description:
    This module performs the upgrade of the exchange rate automatically according
    to the period defined on the cronjob set in the XML.

"""
import logging
import xml.etree.ElementTree as ET
import suds
from datetime import datetime
from suds.client import Client
from openerp import models, fields, api
_logger = logging.getLogger(__name__)


class trmColombian(models.Model):
    _inherit = "res.currency.rate"

    def _get_soap_trm(self):
        s_url = "http://obiee.banrep.gov.co/analytics/saw.dll?wsdl"
        o_client = Client(s_url, service="SAWSessionService")
        s_session_id = o_client.service.logon("publico", "publico")
        o_client.set_options(service="XmlViewService")
        s_reportPath = "/shared/Consulta Series Estadisticas desde Excel/1. " \
            "Tasa de Cambio Peso Colombiano/1.1 TRM - " \
            "Disponible desde el 27 de noviembre de 1991/" \
            "1.1.3 Serie historica para un rango de fechas dado"
        o_report = {
            "reportPath": s_reportPath,
            "reportXml": "null"
        }
        o_options = {
            "async": "false",
            "maxRowsPerPage": "100",
            "refresh": "true",
            "presentationInfo": "true"
        }
        try:
            o_result_query = o_client.service.executeXMLQuery(
                o_report, "SAWRowsetData", o_options, s_session_id)
            o_client.set_options(service="SAWSessionService")
            o_client.service.logoff(s_session_id)
            o_xml_data = ET.fromstring(o_result_query.rowset)
            return o_xml_data[0][1].text, float(o_xml_data[0][2].text)
        except suds.WebFault as detail:
            o_client.set_options(service="SAWSessionService")
            o_client.service.logoff(s_session_id)
            _logger.critical(
                "Error while working with BancoRep API: " + detail)
            return "", 0.0

    @api.model
    def get_colombian_trm(self):
        o_name_currency_taget = ("COP", "cop")
        s_name_rate, f_trm_val = self._get_soap_trm()
        """
            In case records do not exist for the currency indicated in the
            tuple o_name_currency_taget, it will be impossible to gain access
            to the index [0] of the records returned
            (0 records - IndexError: tuple index out of range).
            If the currency does not exist, the id of the currency to work
            will take a None Value and after a message will apper in the log
            file indicating that the currency does not exist.
        """
        try:
            i_currency_id = self.env["res.currency"].search(
                [("name", "in", o_name_currency_taget)])[0].id
        except:
            i_currency_id = None
        if i_currency_id != None:
            """
                In the event that the currency exists, but does not have any
                records of exchange rate, the code will work in the same
                way that he worked with the validation of the currency.
                (If any record returned s_name_last_rate will be a real value,
                if no records returned - Exception case, the default
                value will be '0' in terms of Date Field)
            """
            try:
                s_name_last_rate = self.search(
                [("currency_id", "=", i_currency_id)], limit=1, order="name desc")[0].name
            except:
                s_name_last_rate = "0000-00-00 00:00:00"
            if f_trm_val > 0.0 and s_name_rate != s_name_last_rate[0: -9]:
                o_vals = {
                "rate": f_trm_val,
                "name": datetime.strptime(s_name_rate, "%Y-%m-%d"),
                "currency_id": i_currency_id
                }
                self.create(o_vals)
                _logger.info(
                    "New exchange rate created to date: " +
                    s_name_rate +
                    ", with value: " +
                    str(f_trm_val)
                )
            else:
                _logger.critical(
                    "Already exist TRM for the date " +
                    s_name_rate
                )
        else:
            _logger.critical(
                "Cannot create exchange rate record for currency " +
                o_name_currency_taget[0] +
                " - " +
                o_name_currency_taget[1] +
                ". The currency does not exist."
            )
