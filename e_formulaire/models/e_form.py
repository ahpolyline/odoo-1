# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime, date, timedelta, time
from dateutil.rrule import rrule, DAILY
from pytz import timezone, UTC
from odoo.exceptions import Warning, UserError


class EFormulaire(models.Model):
    _name = 'e.formulaire'
    _description = 'E-Formulaure'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'

    number = fields.Char(string='Numéro',
        copy=False, default="Nouveau", readonly=True)
    info_complementaire = fields.Char(string='Information complémentaire',
        required=False)
    observation = fields.Text(string='Observation',
        required=False)
    note = fields.Text(string='Note',
        required=False)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Entreprise', ondelete='restrict',
        domain="['|', ('parent_id','=', False), ('is_company','=',True)]",
        check_company=True)
    rccm = fields.Char(string='RCCM',related='partner_id.rccm',
        required=False)
    ifu = fields.Char( string='numéro ifu',related='partner_id.vat',
        required=False)
    raison_sociale = fields.Char(string='Raison sociale',
        required=False)
    national_societe = fields.Char(string='Nationalité de la société',
        required=False)
    validation_type = fields.Selection(string='Type de Validation', related='e_formulaire_type_id.validation_type',
                                       readonly=False)
    date_request = fields.Date(string='Date de requête',default=fields.Date.context_today, store=True, required=True)
    date_approbation = fields.Date(string='Date d\'Approbation', store=True, required=False)
    duration_unit = fields.Selection(related='e_formulaire_type_id.duration_unit', readonly=True)
    duree_validite = fields.Integer(related='e_formulaire_type_id.duree_validite',string='Durée de validité',
        required=False)
    date_exper = fields.Date(string='Dated\'expiration', # compute='_compute_date_experation',
                             required=False)
    duree_validite_renouv = fields.Integer(string='Durée de validité renouvellement',
        required=False)
    form_category = fields.Selection(
        string='Catégorie de formulaire',
        selection=[('carte_immat', 'Care d\'immatriculation'),
                   ('import_product', 'Agrément d\'importation'),
                   ('autorisation_instal_ind','autorisation d\'installation industrielle'),
                   ('prorogation','autorisation de prorogation de succursale')],
        required=False, )
    state = fields.Selection([('draft', 'Nouveau'),
                              ('soumis', 'Nouvelle demande'),
                              ('en_cour', 'En cours de traitement'),
                              ('a_payer', 'En attente de paiement'),
                              ('suspendu', 'Suspendu'),
                              ('rejeter', 'Rejeter'),
                              ('auto_annulé', 'Auto-annulé'),
                              ('confirm','à Approuver'),
                              ('approuve','Approuvé'),
                              ('revoque','Révoqué'),
                              ('expiré', 'Expiré'),
                              ('annuler', ('Annuler'))],
                             default='draft',
                             track_visibility='onchange', )
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, default=lambda self: self.env.uid, readonly=True)
    manager_id = fields.Many2one('hr.employee', compute='_compute_from_employee_id', store=True, readonly=False)
    employee_id = fields.Many2one(
        'hr.employee', compute='_compute_from_formulaire_type', store=True, string='Responsable', index=True, readonly=False,
        ondelete="restrict",
        states={'annuler': [('readonly', True)], 'rejeter': [('readonly', True)], 'a_payer': [('readonly', True)],
                'approuver': [('readonly', True)],
                'en_cour': [('readonly', True)]},
        tracking=True)
    department_id = fields.Many2one('hr.department', compute='_compute_from_formulaire_type',
    string = 'Departement/service',index=True, readonly=False,
        ondelete="restrict",
        states={'annuler': [('readonly', True)], 'rejeter': [('readonly', True)], 'a_payer': [('readonly', True)],
                'approuver': [('readonly', True)],
                'en_cour': [('readonly', True)]},
        tracking=True)

    e_formulaire_type_id = fields.Many2one(
        'e.formulaire.type', compute='_compute_from_employee_id', store=True, string="Type de Formulaire", required=True,
        readonly=False,
        states={'annuler': [('readonly', True)], 'rejeter': [('readonly', True)], 'a_payer': [('readonly', True)],'approuver': [('readonly', True)],
                'en_cour': [('readonly', True)]},
        # domain=[('valid', '=', True)]
    )
    first_approver_id = fields.Many2one(
        'hr.employee', string='Première approbation', readonly=True, copy=False)
    niveau1 = fields.Boolean(string='Niveau1', required=False, default=False)

    multi_form_validation = fields.Boolean(
        string='Multiple Approbation',
        related='e_formulaire_type_id.multi_form_validation',)

    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    payer = fields.Boolean(
        string='Payer',
        required=False)

    def write(self, vals):
        if any(state != 'draft' for state in set(self.mapped('state'))):
            raise UserError(_("Pas de Modification"))
        else:
            return super().write(vals)

    # _sql_constraints = [
    #     ('type_value',
    #      "CHECK((form_type='employee' AND employee_id IS NOT NULL) or "
    #      "(form_type='company' AND partner_id IS NOT NULL) or "
    #      "(form_type='department' AND department_id IS NOT NULL) )",
    #      "L'employé, le service ou l'entreprise de cette demande est manquant. Veuillez vous assurer que votre login d'utilisateur est lié à un employé."),
    #     ('date_check2', "CHECK ((date_request <= date_exper))", "La date de début doit être antérieure à la date de fin."),
    # ]
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(
                    _('Vous ne pouvez pas supprimer un formulaire non Brouillon'))
        return super(MissionExterne, self).unlink()

    @api.model
    def create_inst_indus(self, vals):
        vals['number'] = self.env['ir.sequence'].next_by_code(
            'installation.indust.seq') or _('Nouveau')
        res = super(EFormulaire, self).create(vals)
        return res

    @api.depends('e_formulaire_type_id')
    def _compute_state(self):
        for form in self:
            if self.env.context.get('unlink') and form.state == 'draft':
                form.state = 'draft'
            else:
                form.state = 'confirm' if form.validation_type != 'no_validation' else 'draft'

    @api.depends('e_formulaire_type_id')
    def _compute_from_formulaire_type(self):
        for rec in self:
            emplyee = rec.e_formulaire_type_id.assigner
            departement = rec.e_formulaire_type_id.department_id
            if rec.e_formulaire_type_id:
                rec.employee_id = emplyee
                rec.department_id = departement
            else:
                rec.employee_id = rec.employee_id
                rec.department_id = rec.department_id

    @api.depends('employee_id')
    def _compute_from_employee_id(self):
        for rec in self:
            rec.manager_id = rec.employee_id.parent_id.id
            if rec.employee_id.user_id != self.env.user and self._origin.employee_id != rec.employee_id:
                rec.e_formulaire_type_id = False


    # @api.onchange('date_request', 'duree_validite')
    # def _check_change(self):
    #     if self.date_request:
    #         end_date = (date.today() + timedelta(self.duree_validite))
    #         self.date_exper = end_date

    def action_approve(self):
        for rec in self:
            current_user = rec.env.user
            if current_user.has_group('e_formulaire.group_e_formulaire_manager') or current_user.has_group('e_formulaire.group_e_formulaire_responsibler'):
                rec.state ='approuve'
                rec.date_approbation = fields.Date.today()
                rec.date_exper = rec.date_approbation + timedelta(rec.duree_validite)
            else:
                raise UserError(_(
                    'Veuillez connecter avec le responsable autorisé de valider finale de cette demande.'))

    def action_valider(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        resp_niveau1 = self.e_formulaire_type_id.first_validateor_id
        resp_niveau2 = self.e_formulaire_type_id.second_validateor_id
        for rec in self:
            if rec.multi_form_validation == False:
                if rec.employee_id != current_employee:
                    raise UserError(_(
                        'Veuillez connecter avec le responsable autorisé de valider cette demande.'))
                else:
                    rec.state = 'confirm'
            elif rec.multi_form_validation == True and rec.niveau1 == False and current_employee != resp_niveau1:
                raise UserError(_(
                    'Veuillez connecter avec le responsable niveau 1.'))
            elif rec.multi_form_validation == True and rec.niveau1 == False and current_employee == resp_niveau1:
                rec.niveau1 = True
                rec.state = 'en_cour'
            elif rec.state == 'en_cour' and current_employee != resp_niveau2:
                raise UserError(_(
                    'Vuillez connecter avec le responsable niveau 2.'))
            else:
                rec.state = 'confirm'