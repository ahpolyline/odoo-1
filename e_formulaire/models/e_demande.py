# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, api
from lxml import etree
import json as simplejson
import re
import base64
import datetime
from datetime import timedelta, datetime
from odoo import SUPERUSER_ID
from odoo.http import request

from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError, ValidationError, RedirectWarning

from odoo.http import request
from .res_company import GenerateQrCode
from odoo.tools import html2plaintext

_TASK_STATE = [
    ("draft", "Draft"),
    ("soumis","Soumis"),
    ('en_traitement', 'En Traitement'),
    ("encour_1", "En traitement 1"),
    ("encour_2", "En Cours Niveau 2"),
    ("suspendu", 'Suspendu'),
    ("revoque", "Révoqué"),
    ("a_approuver", "En traitement 2"),
    ("approuver", "Approuvé"),
    ('renouvel', 'Renouvellement'),
    ("cancelled", "Rejeté"),
]


class Task(models.Model):
    _inherit = 'project.task'
    _description = 'e-Demandes'

    def get_message(self):
        if self.env.context.get('message', False):
            return self.env.context.get('message')
        return False

    state = fields.Selection(related="stage_id.state", store=True)
    stage_id = fields.Many2one('project.task.type', string='Stage', compute='_compute_stage_id',
                               store=True, readonly=False, ondelete='restrict', tracking=True, index=True,
                               domain="[('project_ids', '=', project_id)]", copy=False)
    info_complementaire = fields.Char(string='Information complémentaire',
                                      required=False)
    message = fields.Text('Message', readonly=True, default=get_message)
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
    gerant = fields.Char('Gérant', related='partner_id.resp', )
    date_naissance = fields.Date('Date de Naissance', related='partner_id.date_naissance')
    lieu_naissance = fields.Char('Lieu de naissance', related='partner_id.lieu_naissance')
    nationalie_gerant = fields.Char('Nationité', related='partner_id.nationality')
    date_request = fields.Date(string='Date de requête', default=fields.Date.context_today, store=True, required=True)
    date_confirm1 = fields.Date(string='Date de Confirmation', readonly=True, copy=False, )
    confirmer_par = fields.Many2one('hr.employee',
                                    string='Confirmée par', readonly=True,
                                    copy=False)
    date_approbation = fields.Date(string='Date d\'Approbation', store=True, required=False)
    approuver_par = fields.Many2one('hr.employee',
                                    string='Approuvée par', readonly=True,
                                    copy=False)
    date_suspension = fields.Date(string='Date de suspension', readonly=True, copy=False, )
    suspendre_par = fields.Many2one('hr.employee',
                                    string='Suspendu par', readonly=True,
                                    copy=False)
    date_reject = fields.Date(string='Date de Rejet', readonly=True, )
    rejeter_par = fields.Many2one('hr.employee',
                                  string='Rejetée par', readonly=True,
                                  copy=False)
    date_revocation = fields.Date(string='Date de révocation', readonly=True, copy=False, )
    revoquer_par = fields.Many2one('hr.employee',
                                   string='Révoquée par', readonly=True,
                                   copy=False)
    date_exper = fields.Date(string='Date d\'expiration',
                             required=False)
    duree_validite = fields.Integer(related='project_id.duree_validite', string='Durée de validité',
                                    required=False)
    duree_validite_renouv = fields.Integer(string='Durée de validité renouvellement',
                                           required=False)
    duration_unit = fields.Selection(related='project_id.duration_unit', readonly=True)
    renouvellement = fields.Selection([('non', 'Non'),
                                       ('oui', 'Oui')],
                                      string='Renouvelable', related='project_id.renouvellement', default='non', )
    custome_code = fields.Char(string='Code', related='project_id.custome_code', required=True)
    multi = fields.Boolean(
        string='Multi', related='project_id.multi',
        required=False)
    first_approver_id = fields.Many2many('hr.employee', related='project_id.employee1_ids',
                                         string='Première approbation', readonly=True, copy=False)
    secend_approver_id = fields.Many2many('hr.employee', related='project_id.employee2_ids',
                                          string='Deuxiéme approbation', readonly=True, copy=False)
    assign_to1 = fields.Many2one('hr.employee', string='Assigné à', ondelete='cascade', index=True, copy=False)
    assign = fields.Many2one('hr.employee', string='Assigné à', ondelete='cascade', index=True, copy=False)
    date_assigne = fields.Date(string='Date', readonly=True, copy=False, )
    assign_to2 = fields.Many2one('hr.employee', string='Assigné à', ondelete='cascade', index=True, copy=False)
    responsable_depart = fields.Many2one('hr.employee', related='project_id.responsable_depart',
                                         string='Responsable_ départ', required=False)
    demande_alerte = fields.Boolean("Alerte")
    template_id = fields.Many2one('mail.template', string='Email Template', domain="[('model','=','project.task')]",
                                  required=False)
    number = fields.Char(string='Number', readonly=True, )
    type_form = fields.Selection(
        string='Type de formulaire', related='project_id.type_form', )
    produit = fields.Char(string='Nom de produit', required=False)
    country_id = fields.Many2one('res.country', string='Country',)
    provenance = fields.Char(string='Provenance', ondelete='restrict')
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")
    montant = fields.Float(string='Montant', digits=(6, 2))
    capital = fields.Float('Capital social', related='partner_id.capital')
    doc1 = fields.Binary("Upload file1")
    doc1_name = fields.Char('File Name')
    doc2 = fields.Binary("Upload file2")
    doc2_name = fields.Char('File Name2')
    doc3 = fields.Binary("Upload file3")
    doc3_name = fields.Char('File Name3')
    doc4 = fields.Binary("Upload file4")
    doc4_name = fields.Char('File Name4')
    t1 = fields.Boolean('T1', default=False)
    t2 = fields.Boolean('T2', default=False)
    s1 = fields.Boolean('S1', default=False)
    s2 = fields.Boolean('S2', default=False)

    # @api.constrains('doc1','doc2','doc3','doc4')
    # def _check_file(self):
    #     docs = {self.doc1_name, self.doc2_name, self.doc3_name, self.doc4_name}
    #     if any(str(doc.split(".")[1]) != 'pdf' for doc in docs):
    #         raise ValidationError("Impossible de télécharger un fichier différent du fichier .pdf")

    # def write(self, vals):
    #     if any(state == 'en_traitement' for state in set(self.mapped('state'))):
    #         raise UserError(_("No edit in done state"))
    #     else:
    #         return super().write(vals)

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('task.order.seq')
        vals.update({
            'number': number
        })
        return super(Task, self).create(vals)

    # def unlink(self):
    #     if any(demande.env.user.has_group('base.group_system') for demande in self):
    #         raise UserError('Vous n\'avez pas le droit de suprimer la demande!!')
    #     return super().unlink()

    def action_traiter(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if rec.state == 'soumis':
                if rec.env.user.has_group(
                        'base.group_erp_manager') or rec.responsable_depart == current_employee or (rec.assign_to1 and rec.assign_to1 == current_employee) or current_employee == rec.first_approver_id:
                    action_traiter = self.env['project.task.type'].search([('state', '=', 'en_traitement')], limit=1)
                    rec.write({
                        'stage_id': action_traiter and action_traiter.id or None
                    })
                    rec.state = 'en_traitement'
                    rec.assign = current_employee
                    rec.date_assigne = fields.Date.today()
                    rec.t1 = True
                    rec.s1 = True
                else:
                    raise UserError(_(
                        'Veuillez-vous connecter avec le responsable autorisé à approuver cette demande.'))
            elif rec.state == 'a_approuver':
                if rec.env.user.has_group(
                        'base.group_erp_manager') or rec.responsable_depart == current_employee or (rec.assign_to2 and rec.assign_to2 == current_employee) or current_employee == rec.secend_approver_id:
                    action_traiter = self.env['project.task.type'].search([('state', '=', 'en_traitement')], limit=1)
                    rec.write({
                        'stage_id': action_traiter and action_traiter.id or None
                    })
                    rec.state = 'en_traitement'
                    rec.assign = current_employee
                    rec.date_assigne = fields.Date.today()
                    rec.t2 = True
                    rec.s2 = True
                else:
                    raise UserError(_(
                        'Veuillez-vous connecter avec le responsable autorisé à approuver cette demande.'))

    def confirm1(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if rec.env.user.has_group(
                        'base.group_erp_manager') or rec.responsable_depart == current_employee or rec.assign == current_employee:
                confirm1 = self.env['project.task.type'].search([('state', '=', 'a_approuver')], limit=1)
                rec.write({
                    'stage_id': confirm1 and confirm1.id or None
                })
                rec.state = 'a_approuver'
                rec.confirmer_par = current_employee
                rec.date_confirm1 = fields.Date.today()
                rec.assign = None
                rec.date_assigne = None
                rec.t1 = False
                rec.s1 = False
            else:
                raise UserError(_(
                    'Veuillez-vous connecter avec le responsable autorisé à approuver cette demande!!'))

    def action_approve(self):
        self.ensure_one()
        template_id = self.env.ref('e_formulaire.email_dii_email_template').id
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if rec.env.user.has_group(
                    'base.group_erp_manager') or rec.responsable_depart == current_employee or rec.assign == current_employee:
                confirm2 = self.env['project.task.type'].search([('state', '=', 'approuver')], limit=1)
                rec.write({
                    'stage_id': confirm2 and confirm2.id or None
                })
                rec.state = 'approuver'  # Status approuver
                rec.date_approbation = fields.Date.today()
                rec.date_exper = rec.date_approbation + timedelta(rec.duree_validite)
                rec.approuver_par = current_employee
                rec.assign = None
                rec.date_assigne = None
                rec.t2 = False
                rec.s2 = False
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
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for rec in self:
            if rec.s1 == True:
                if rec.env.user.has_group(
                        'base.group_erp_manager') or rec.responsable_depart == current_employee or rec.assign == current_employee:
                    if rec.observation:
                        suspendre = self.env['project.task.type'].search([('state', '=', 'suspendu')], limit=1)
                        rec.write({
                            'stage_id': suspendre and suspendre.id or None
                        })
                        rec.state = 'suspendu'
                        rec.suspendre_par = current_employee
                        rec.date_suspension = fields.Date.today()
                        rec.s1 = False
                    else:
                        raise UserError(_(
                            'Veuillez montionner le motif de la suspension !!'))
                else:
                    raise UserError(_(
                        'Veuillez connecter avec le bon utilisateur !!'))

    def revoquer(self):
        for rec in self:
            if rec.state != 'revoque':
                revoquer = self.env['project.task.type'].search([('state', '=', 'revoque')], limit=1)
                rec.write({
                    'stage_id': revoquer and revoquer.id or None
                })
                rec.state = 'revoque'
                rec.revoquer_par = concurrent
                rec.date_revocation = fields.Date.today()

    def annuler(self):
        for rec in self:
            if rec.state != 'cancelled':
                annuler = self.env['project.task.type'].search([('state', '=', 'annuler')], limit=1)
                rec.write({
                    'stage_id': annuler and annuler.id or None
                })
                rec.state = 'cancelled'
                rec.rejeter_par = concurrent
                rec.date_reject = fields.Date.today()

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
