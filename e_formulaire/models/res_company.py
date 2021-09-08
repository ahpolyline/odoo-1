# -*- coding: utf-8 -*-
import qrcode
import base64
from io import BytesIO
import logging
from typing import Sequence

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FormQrFields(models.Model):
    _name = 'form.qr.fields'
    _order = 'sequence'

    sequence = fields.Integer()
    field_id = fields.Many2one('ir.model.fields', domain=[('model_id.model', '=', 'project.task'),
                                                          ('ttype', 'not in', ['many2many', 'one2many', 'binary'])])
    company_id = fields.Many2one('res.company')


class ResCompany(models.Model):
    _inherit = 'res.company'

    form_qr_type = fields.Selection([('by_url', 'Demande Url'), ('by_info', 'Form Text Information')], default='by_url',
                                    required=True)
    form_field_ids = fields.One2many('form.qr.fields', 'company_id', string="Form Field's")
    fax = fields.Char('Fax')

    @api.constrains('form_field_ids', 'form_qr_type')
    def check_form_field_ids(self):
        if self.form_qr_type == 'by_info' and not self.form_field_ids:
            raise UserError(_("Please Add Form Field's"))


class GenerateQrCode():
    def generate_qr_code(url):
        qr = qrcode.QRCode(
            version=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_img = base64.b64encode(temp.getvalue())
        return qr_img
