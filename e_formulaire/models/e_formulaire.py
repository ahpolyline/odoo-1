# -*- coding: utf-8 -*-

import ast
from datetime import timedelta, datetime
from random import randint

from odoo import api, fields, models, tools, SUPERUSER_ID, _


class FormConfig(models.Model):
    _inherit = 'project.project'
    _description = 'form.config'

    def _get_default_type_common(self):
        ids = self.env["project.task.type"].search([("case_default", "=", True)])
        return ids

    type_form = fields.Selection(
        string='Type de formulaire',
        selection=[('1', 'Demande d\'autorisation d\'installation industrielle'),
                   ('2', 'Demande d\'autorisation de prorogation de succursale'),
                   ('3', 'Attestation tenant lieu de carte d\'importateur'),
                   ('4', 'Demande de carte d\'importateur')],
        required=False, )
    form_image = fields.Binary(),
    type_ids = fields.Many2many(default=lambda self: self._get_default_type_common())
    responsable_depart = fields.Many2one('hr.employee', string='Chef de  Département', index=True, tracking=True)
    employee1_ids = fields.Many2many('hr.employee', 'employee1_form_type_rel', 'form1_type_id', 'emp1_id', string='Approbation Niveau 1')
    employee2_ids = fields.Many2many('hr.employee', 'employee2_form_type_rel', 'form2_type_id', 'emp2_id', string='Approbation Niveau 2')
    multi = fields.Boolean( string='Multi Validation', default=True,required=False)
    duree_validite = fields.Integer(string='Durée de validité', required=False, default='90')
    duration_unit = fields.Selection([('jours', 'Jours'),
                                      ('mois', 'Mois'),
                                      ('ans', 'ans')],
                                      default='jours', string='Durée', required=True)
    duree_validite_renouv = fields.Integer(string='Durée de validité renouvellement', required=False)
    renouvellement = fields.Selection([('non', 'Non'),
                                       ('oui', 'Oui')],
                                      default='non', string='Renouvelable')
    custome_code = fields.Char(string='Code', required=True)
    digital_signature = fields.Binary(string="Signature")
    image_sign = fields.Binary(string='Signature')
    form_link = fields.Char('Link', compute='_form_link')

    @api.depends('type_form')
    def _form_link(self):
        for rec in self:
            if rec.type_form == '1':
                rec.form_link = '/formulaire/demande-autorisation-installation-industrielle'
            elif rec.type_form == '2':
                rec.form_link = '/formulaire/Demande-autorisation-prorogation-succursale'
            elif rec.type_form == '3':
                rec.form_link = '/formulaire/attestation-tenant-lieu-carte-importateur'
            elif rec.type_form == '4':
                rec.form_link = '/formulaire/demande-carte-importateur'
