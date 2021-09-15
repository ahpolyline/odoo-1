# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re
import base64
import  datetime
from datetime import timedelta, datetime
from odoo import SUPERUSER_ID
from odoo.http import request

from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError, ValidationError, RedirectWarning

from odoo.http import request
from . res_company import GenerateQrCode
from odoo.tools import html2plaintext

_TASK_STATE = [
    ("draft", "Nouveau"),
    ("encour_1", "En Cours Niveau 1"),
    ("encour_2", "En Cours Niveau 2"),
    ("suspendu", 'Suspendu'),
    ("revoque", "Révoqué"),
    ("a_approuver", "A Approuver"),
    ("approuver", "Approuver"),
    ('renouvel','Renouvellement'),
    ("cancelled", "Rejeté"),
]


class Task(models.Model):
    _inherit = 'project.task'
    _description = 'e-Demandes'

    state = fields.Selection(_TASK_STATE, related="stage_id.state", store=True)
    # stage_id = fields.Many2one('project.task.type', string='Stage', compute='_compute_stage_id',
    #                            store=True, readonly=False, ondelete='restrict', tracking=True, index=True,
    #                            default=_get_default_stage_id, group_expand='_read_group_stage_ids',
    #                            domain="[('project_ids', '=', project_id)]", copy=False)
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
    date_exper = fields.Date(string='Date d\'expiration',
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
    assign_to1 = fields.Many2one('hr.employee', string='Assigné à',ondelete='cascade', index=True, copy=False)
    assign_to2 = fields.Many2one('hr.employee', string='Assigné à',ondelete='cascade', index=True, copy=False)
    responsable_depart = fields.Many2one('hr.employee', related='project_id.responsable_depart', string='Responsable_ départ',  required=False)
    demande_alerte = fields.Boolean("Alerte")
    template_id = fields.Many2one('mail.template', string='Email Template', domain="[('model','=','project.task')]",
                                  required=False)
    number = fields.Char(string='Number', readonly=True, )


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
                    'Veuillez-vous connecter avec le responsable autorisé à valider cette demande.'))
            else:
                if rec.env.user.has_group('root.base_user') or rec.assign_to1 and rec.assign_to1 == current_employee:

                    rec.write({
                        'state': 'encour_2'

                    })
                      # id stage_id (en cours niveau 2)

                elif rec.assign_to1 and rec.assign_to1 != current_employee:
                    raise UserError(_(
                        'Veuillez-vous connecter avec le responsable autorisé à valider cette demande.'))
                elif not rec.assign_to1:
                    if current_employee not in rec.first_approver_id:
                        raise UserError(_(
                            'Veuillez-vous connecter avec le responsable niveau 1.'))
                    elif current_employee in rec.secend_approver_id:
                        raise UserError(_(
                            'Veuillez-vous connecter avec un responsable autorisé à valider cette demande.'))
                    elif current_employee in rec.first_approver_id:
                        rec.state = 'encour_2'  # id stage_id (en cours niveau 2)

    def confirm2(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if rec.assign_to2 and rec.assign_to2 == current_employee:
                rec.state = 'a_approuver'  # id stage_id (a approuver)

            elif rec.assign_to2 and rec.assign_to2 != current_employee:
                raise UserError(_(
                    'Veuillez-vous connecter avec le responsable autorisé à valider cette demande.'))
            elif not rec.assign_to2:
                if current_employee not in rec.secend_approver_id:
                    raise UserError(_(
                        'Veuillez-vous connecter avec le responsable niveau 2.'))
                elif current_employee in rec.secend_approver_id:
                    rec.state = 'a_approuver'

    # def action_send_mail(self):
    #     self.ensure_one()
    #     template_id = self.env.ref('e_formulaire.email_dii_email_template').id
    #     ctx = {
    #         'default_model': 'project.task',
    #         'default_res_id': self.id,
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_composition_mode': 'comment',
    #         'custom_layout': 'mail.mail_notification_light',
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def action_approve(self):
        self.ensure_one()
        template_id = self.env.ref('e_formulaire.email_dii_email_template').id
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if current_employee == rec.responsable_depart:
                rec.state = 'approuver'  # Status approuver
                rec.date_approbation = fields.Date.today()
                rec.date_exper = rec.date_approbation + timedelta(rec.duree_validite)
                ctx = {
                    'default_model': 'project.task',
                    'default_res_id': self.id,
                    'default_use_template': bool(template_id),
                    'default_template_id': template_id,
                    'default_composition_mode': 'comment',
                    'custom_layout': 'mail.mail_notification_light',
                }
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'target': 'new',
                    'context': ctx,
                }
            else:
                raise UserError(_(
                    'Veuillez-vous connecter avec le responsable autorisé à approuver cette demande.'))

    def suspendre(self):
        for rec in self:
            if (rec.state == rec.state == 'a_approuver' or rec.state == 'encour_2' or rec.state == 'encour_1') and rec.observation:
                rec.state = 'suspendu'
            else:
                raise UserError(_(
                    'Veuillez montionner le motif de la suspension !!'))


    def revoquer(self):
        for rec in self:
            if rec.state != 'revoque':
                rec.state = 'revoque'

    def annuler(self):
        for rec in self:
            if rec.state != 'cancelled':
                rec.state = 'cancelled'

    def retour_to_draft(self):
        for rec in self:
            rec.state = 'encour_1'


    @api.model
    def _cron_date_experation_reminder(self):

        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        for task in self.env['project.task'].search([('date_exper', '!=', None), ('partner_id', '!=', None)]):

            reminder_date = task.date_exper
            today = datetime.now().date()
            diff = reminder_date - today
            if diff == 8 and task:
                template_id = self.env['ir.model.data'].get_object_reference(
                    'e_formulaire',
                    'email_template_renouvellement_reminder')[1]
                if template_id:
                    email_template_obj = self.env['mail.template'].browse(template_id)
                    values = email_template_obj.generate_email(task.id,
                                                               ['subject', 'body_html', 'email_from', 'email_to',
                                                                'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
                    msg_id = self.env['mail.mail'].create(values)
                    if msg_id:
                        msg_id._send()

        return True

    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')

    def _generate_qr_code(self):
        qr_code = ''
        if self.env.user.company_id.form_field_ids != 'by_info':
            qr_info = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            qr_info += self.get_portal_url()
        else:
            if self.env.user.company_id.form_field_ids:
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



