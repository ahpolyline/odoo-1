# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re
import base64

from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError, ValidationError, RedirectWarning
from datetime import timedelta
from odoo.http import request
from . res_company import GenerateQrCode
from odoo.tools import html2plaintext


class Task(models.Model):
    _inherit = 'project.task'
    _description = 'e-Demandes'

    state = fields.Selection(related="stage_id.state", store=True)
    info_complementaire = fields.Char(string='Information complémentaire',
                                      required=False)
    observation = fields.Text(string='Observation',
                              required=False)
    note = fields.Text(string='Note',
                       required=False)
    partner_id = fields.Many2one('res.partner', string='Entreprise', check_company=True)
    rccm = fields.Char(string='RCCM', related='partner_id.rccm',
                       required=False)
    ifu = fields.Char(string='numéro ifu', related='partner_id.vat',
                      required=False)
    raison_sociale = fields.Char(string='Raison sociale',
                                 required=False)
    national_societe = fields.Char(string='Nationalité de la société', related='partner_id.country_id.name',
                                   required=False)
    date_request = fields.Date(string='Date de requête', default=fields.Date.context_today, store=True, required=True)
    date_approbation = fields.Date(string='Date d\'Approbation', store=True, required=False)
    duration_unit = fields.Selection(related='project_id.duration_unit', readonly=True)
    duree_validite = fields.Integer(related='project_id.duree_validite', string='Durée de validité',
                                    required=False)
    date_exper = fields.Date(string='Dated\'expiration',
                             required=False)
    duree_validite_renouv = fields.Integer(string='Durée de validité renouvellement',
                                           required=False)
    renouvellement = fields.Selection([('non', 'Non'),
                                       ('oui', 'Oui')],
                                       string='Renouvelable', related='project_id.renouvellement', default='non',)
    custome_code = fields.Char(string='Code', related='project_id.custome_code', required=True)
    multi = fields.Boolean(
        string='Multi', related='project_id.multi',
        required=False)
    first_approver_id = fields.Many2many('hr.employee', related='project_id.employee1_ids',
                                         string='Première approbation', readonly=True, copy=False)
    secend_approver_id = fields.Many2many('hr.employee', related='project_id.employee2_ids',
                                          string='Deuxiéme approbation', readonly=True, copy=False)
    assign_to1 = fields.Many2one('hr.employee', string='Assigné à',
                                 index=True, tracking=True)
    assign_to2 = fields.Many2one('hr.employee',
                                 string='Assigné à',
                                 index=True, tracking=True)
    demande_alerte = fields.Boolean("Alerte")
    template_id = fields.Many2one('mail.template', string='Email Template', domain="[('model','=','project.task')]",
                                  required=False)
    number = fields.Char(string='Number', readonly=True, )
    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')

    def preview_attest(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('task.order.seq')
        vals.update({
            'number': number
        })
        return super(Task, self).create(vals)

    def confirm1(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if not rec.multi:
                raise UserError(_(
                    'Veuillez connecter avec le responsable autorisé de valider cette demande.'))
            else:
                if rec.assign_to1 and rec.assign_to1 == current_employee:

                    rec.state = 'encour_2'  # id stage_id (en cours niveau 2)

                elif rec.assign_to1 and rec.assign_to1 != current_employee:
                    raise UserError(_(
                        'Veuillez connecter avec le responsable autorisé de valider cette demande.'))
                elif not rec.assign_to1:
                    if current_employee not in rec.first_approver_id:
                        raise UserError(_(
                            'Veuillez connecter avec le responsable niveau 1.'))
                    elif current_employee in rec.secend_approver_id:
                        raise UserError(_(
                            'Veuillez connecter avec un responsable autorisé de valider cette demande.'))
                    elif current_employee in rec.first_approver_id:
                        rec.state = 'encour_2'  # id stage_id (en cours niveau 2)

    def confirm2(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if rec.assign_to2 and rec.assign_to2 == current_employee:
                rec.state = 'a_approuver'  # id stage_id (a approuver)

            elif rec.assign_to2 and rec.assign_to2 != current_employee:
                raise UserError(_(
                    'Veuillez connecter avec le responsable autorisé de valider cette demande.'))
            elif not rec.assign_to2:
                if current_employee not in rec.secend_approver_id:
                    raise UserError(_(
                        'Veuillez connecter avec le responsable niveau 2.'))
                elif current_employee in rec.secend_approver_id:
                    rec.state = 'a_approuver'

    def action_approve(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        #    template_id = self.env.ref('e_formulaire.email_template_xml_id').id
        for rec in self:
            if current_employee:
                rec.state = 'approuver'  # Status approuver
                rec.date_approbation = fields.Date.today()
                rec.date_exper = rec.date_approbation + timedelta(rec.duree_validite)
            else:
                raise UserError(_(
                    'Veuillez connecter avec le responsable autorisé d\'appreouver cette demande.'))

    def suspendre(self):
        for rec in self:
            if rec.state == 'approuver' or rec.state == 'a_approuver' or rec.state == 'encour_2' or rec.state == 'encour_1':
                rec.state = 'suspendu'

    @api.model
    def _alert_renouvellement(self):
        for alert in self.env['project.tast'].search([('date_exper', '!=', None), ('renouvellement', '==', 'oui')]):
            remined = alert.date_exper
            tody = datetime.now().date()
            if remined == tody and alert:
                template_id = self.env['ir.model.data'].get_object_reference(
                             'task_deadline_reminder',
                             'email_template_edi_deadline_reminder')[1]
    #
    # def btn_send_mail(self):
    #     report_template_id = self.env.ref('e_formulaire.dii_email_template').id
    #     template = self.env['mail.template'].browse(report_template_id)
    #     template.send_mail(self.id, force_send=True)

    # @api.model
    # def _demande_alerte(self):

        # for alert in self.env['project.task'].search([('date_exper', '!=', None),
        #                                               ('task_reminder', '=', True), ('user_id', '!=', None)]):
        #
        #     reminder_date = task.date_deadline
        #     today = datetime.now().date()
        #     if reminder_date == today and task:
        #         template_id = self.env['ir.model.data'].get_object_reference(
        #             'task_deadline_reminder',
        #             'email_template_edi_deadline_reminder')[1]
        #         if template_id:
        #             email_template_obj = self.env['mail.template'].browse(template_id)
        #             values = email_template_obj.generate_email(task.id,
        #                                                        ['subject', 'body_html', 'email_from', 'email_to',
        #                                                         'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
        #             msg_id = self.env['mail.mail'].create(values)
        #             if msg_id:
        #                 msg_id._send()
        #
        # return True

    def _generate_qr_code(self):
        qr_code = ''
        if self.env.user.company_id.form_field_ids != 'by_info':
            result = self.search_read(
                [('id', 'in', self.ids)],
                self.env.user.company_id.form_field_ids.mapped('field_id.name')
            )
            dict_result = {}
            for field in self.env.user.company_id.form_field_ids.mapped('field_id'):
                if field.ttype == 'many2one':
                    dict_result[field.field_description] = self[field.name].display_name
                else:
                    dict_result[field.field_description] = self[field.name]
                qr_code = html2plaintext(qr_code)
        self.qr_image = GenerateQrCode.generate_qr_code(qr_code)

    def print_dii_report(self):
        return self.env.ref('e_formulaire.dii_attestation_pdf_report').report_action(self)

