# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models, api


class EFormulaireType(models.Model):
    _name = 'e.formulaire.type'
    _description = 'Tyoe de Formulaire'

    name = fields.Char('Type de Formulaire', required=True, translate=True)
    code = fields.Char('Code')
    sequence = fields.Integer(default=100,
                              help='The type with the smallest sequence is the default value in time off request')
    active = fields.Boolean('Active', default=True,
                            help="If the active field is set to false, it will allow you to hide the time off type without removing it.")

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Entreprise',
        required=False)
    rccm = fields.Char(
        string='RCCM',
        required=False)
    ifu = fields.Char(
        string='numéro ifu',
        required=False)
    raison_sociale = fields.Char(
        string='Raison sociale',
        required=False)
    national_societe = fields.Char(
        string='Nationalité de la société',
        required=False)
    date_request = fields.Date(
        string='Date de requête',
        required=False)
    assigner = fields.Many2one('hr.employee',
                               string='Assigner à',
                               required=False,
                               copy=True)
    department_id = fields.Many2one('hr.department',
                                    string='Departement/service',
                                    required=False,
                                    copy=True, )
    duree_validite = fields.Integer(
        string='Durée de validité',
        required=False)
    duration_unit = fields.Selection([
        ('jours', 'Jours'), ('mois', 'Mois'), ('ans', 'ans')],
        default='jours', string='Durée', required=True)
    duree_validite_renouv = fields.Integer(
        string='Durée de validité renouvellement',
        required=False)
    date_exper = fields.Date(
        string='Dated\'expiration',
        required=False)
    user_id = fields.Many2one('res.users', 'Responsible',
                                     domain=lambda self: [
                                         ('groups_id', 'in', self.env.ref('e_formulaire.group_e_formulaire_user').id)])
    validation_type = fields.Selection([
        ('no_validation', 'No Validation'),
        ('hr', 'Valider par un Employée'),
        ('multi', 'Multiple Approbation')], default='hr',)
    renouvellement = fields.Selection([
        ('non', 'Non'),
        ('oui', 'Oui')],
        default='non', string='Renouvelable')
    multi_form_validation = fields.Boolean(
        string='Multiple Approbation', )
    first_validateor_id = fields.Many2one('hr.employee',
                               string='Responsable 1',
                               required=False,
                               copy=True)
    second_validateor_id = fields.Many2one('hr.employee',
                               string='Rsponsable 2',
                               required=False,
                               copy=True)

    @api.onchange('validation_type')
    def enable_multi_form_validation(self):
        self.multi_form_validation = True if (
                self.validation_type == 'multi') else False

    @api.onchange('assigner')
    def set_department(self):
        for rec in self:
            rec.department_id = rec.assigner.sudo().department_id.id


