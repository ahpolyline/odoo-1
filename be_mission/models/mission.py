# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning, UserError
from odoo.addons import decimal_precision as dp
import re


class MissionExterne(models.Model):
    _name = 'mission.externe'
    _description = 'Mission Externe'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Service Number', copy=False, default="Nouveau")
    date = fields.Date(string='Date',
                       default=fields.Date.today(),
                       required=True, readonly=True)
    person_name = fields.Many2one(
        'res.partner', string="Nom et Prénom", required=True)
    employee_id = fields.Many2one('hr.employee', string='Employée',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1),
                                  required=True, copy=True)
    date_depart = fields.Date(
        string='Date de départ', default=fields.Date.context_today, store=True, required=False)
    date_exp = fields.Date(string='Date d\'expiration', required=False)

    date_arriver = fields.Date(
        string='Date d\'arrivée', default=fields.Date.context_today, store=True, required=False)

    passport = fields.Char(string='Numéro du Passeport', required=False)
    objet = fields.Text(string="Objet Mission", required=False)

    visa = fields.Selection(string='Visa', selection=[('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_visa = fields.Date(string='Date', required=False)
    l_invitation = fields.Selection(string='Lettre d\'invitation', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_lettre = fields.Date(
        string='Date',
        required=False)

    post_v = fields.Char(string='Fonction voyageur', required=False)
    chauffeur = fields.Boolean(string='Chauffeur', required=False)
    n_chauffeur = fields.Char(string='Nom du Chauffeur', required=False)
    chauffeur_cont = fields.Char(string='Contact du Chauffeur', required=False)
    matricule = fields.Char(string='Matricule du Véhicule', required=False)
    duree_b = fields.Integer(string='Durée d\'utilisation du Véhicule', required=False)
    responsable = fields.Char(string='Nom personne ressource', required=False)
    post = fields.Char(string='Fonction personne ressource', required=False)

    test_ca = fields.Selection(string='Test COVID', selection=[(
        'oui', 'Oui'), ('non', 'Non')], required=False, )

    date_ca = fields.Date(string='Date de test covid', required=False)

    test_cd = fields.Selection(string='Test COVID', selection=[(
        'oui', 'Oui'), ('non', 'Non')], required=False, )

    date_cd = fields.Date(string='Date de test covid', required=False)

    hotel = fields.Char(string='Nom de l\'hôtel', required=False)
    duree_s = fields.Integer(string='Durée du séjour', required=False)
    duree_h = fields.Integer(string='Durée du séjour hôtel', required=False)
    autres = fields.Char(
        string='Autres',
        required=False)
    commentaire = fields.Text(
        string="Commentaire",
        required=False)

    frais_h = fields.Selection(string='Frais d\'hôtel', selection=[(
        'employee', 'Employée'), ('webb', 'Webb Fontaine'), ('autres', 'Autres')], required=False, )

    point_equi = fields.Text(string='Point Equipement', required=False)
    satisfact = fields.Selection(string='Satisfaction', selection=[('mauv', 'Mauvaise'),
                                                                   ('pass',
                                                                    'Passable'),
                                                                   ('a_bien',
                                                                    'Assez-bien'),
                                                                   ('bien',
                                                                    'Bien'),
                                                                   ('t_bien',
                                                                    'Trés-bien'),
                                                                   ('excel', 'Excelente'), ], required=False, )

    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('arriver', 'Arriver'),
        ('depart', 'Départ'),
        ('terminer', 'Terminé'),
        ('cancel', 'Annulé')],
        default='draft',
        track_visibility='onchange', )
    unity_sejour = fields.Selection([('jours','jours'),
                                     ('semaines','semaines'),
                                     ('mois','mois'),
                                     ('année','années')],
                                    required=False, default='jours')
    unity_sejour_hotel =  fields.Selection([('jours','jours'),
                                     ('semaines','semaines'),
                                     ('mois','mois'),
                                     ('année','années')],
                                    required=False, default='jours')
    unity_duree_vehicule =  fields.Selection([('jours','jours'),
                                     ('semaines','semaines'),
                                     ('mois','mois'),
                                     ('année','années')],
                                             required=False, default='jours')

    def unlink(self):
        for rec in self:
            if rec.state not in  ('draft', 'cancel'):
                raise Warning(
                    _('Vous ne pouvez pas supprimer un formulaire validé'))
        return super(MissionExterne, self).unlink()

    @api.onchange('date_arriver', 'date_ca')
    def onchange_date_arriver_covid(self):
        for rec in self:
            if rec.date_arriver and rec.date_ca and rec.date_arriver < rec.date_ca:
                raise Warning(_('La date "Test Covid" doit être avant la date d\'arrivée'))
            else:
                pass

    @api.onchange('date_depart', 'date_cd')
    def onchange_date_depart_covid(self):
        for rec in self:
            if rec.date_depart and rec.date_cd and rec.date_depart < rec.date_cd:
                raise Warning(_('La date "Test Covid" doit être avant la date de départ'))
            else:
                pass

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'mission.externe') or _('Nouveau')
        res = super(MissionExterne, self).create(vals)
        return res

    def action_arriver(self):
        for rec in self:
            rec.state = 'arriver'

    def action_depart(self):
        for rec in self:
            rec.state = 'depart'

    def action_terminer(self):
        for rec in self:
            rec.state = 'terminer'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'


class MissionInterne(models.Model):
    _name = 'mission.interne'
    _description = 'Mission Interne'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Service Number', copy=False, default="Nouveau")
    date = fields.Date(
        string='Date',
        default=fields.Date.today(),
        required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employée',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1),
                                  required=True, copy=True)
    date_depart = fields.Date(
        string='Date de départ', default=fields.Date.context_today, store=True, required=False)
    date_exp = fields.Date(string='Date d\'expiration', required=False)

    date_retour = fields.Date(
        string='Date de Retour', default=fields.Date.context_today, store=True, required=False)

    passport = fields.Char(string='Numéro du Passeport', required=False)
    objet = fields.Text(string="Objet Mission", required=False)
    o_mission = fields.Selection(string='Ordre de mission', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_mission = fields.Date(
        string='Date de mission',
        required=False)
    billet = fields.Selection(string='Achat Billet d\'avion', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_achat_billet = fields.Date(string='Date achat billet',  required=False)
    visa = fields.Selection(string='Visa', selection=[('oui', 'Oui'), ('non', 'Non')], required=False)
    date_visa = fields.Date(string='Date', required=False)

    l_invitation = fields.Selection(string='Lettre d\'invitation', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )

    date_lettre = fields.Date(string='Date', required=False)

    vehicule = fields.Selection(string='Besoin de véhicule ?', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    n_chauffeur = fields.Char(string='Nom du Chauffeur', required=False)
    chauffeur_cont = fields.Char(string='Contact du Chauffeur', required=False)
    matricule = fields.Char(string='Matricule du Véhicule', required=False)
    duree_b = fields.Integer(string='Durée d\'utilisation du Véhicule', required=False)
    responsable = fields.Char(string='Nom du Responsable', required=False)
    post = fields.Char(string='Poste du responsable', required=False)

    test_cr = fields.Selection(string='Test COVID', selection=[(
        'oui', 'Oui'), ('non', 'Non')], required=False, )
    date_cr = fields.Date(string='Date de test covid', required=False)

    test_cd = fields.Selection(string='Test COVID', selection=[(
        'oui', 'Oui'), ('non', 'Non')], required=False, )
    date_cd = fields.Date(string='Date de test covid', required=False)

    frais_m = fields.Selection(string='Frais de Mission', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_f = fields.Date(string='Date de frais de mission', required=False)
    p_financier = fields.Selection(string='Point financier?', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_pf = fields.Date(string='Date point financier', required=False)
    commentaire = fields.Text(
        string="Commentaire",
        required=False)

    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('depart', 'Départ'),
        ('retour', 'Retour'),
        ('terminer', 'Terminé'),
        ('cancel', 'Annulé')],
        default='draft',
        track_visibility='onchange', )
    #jours = fields.Char(string='Jours', required=False, default='Jours')
    unity_duree_vehicule = fields.Selection([('jours', 'jours'),
                                             ('semaines', 'semaines'),
                                             ('mois', 'mois'),
                                             ('année', 'années')],
                                            required=False, default='jours')

    def unlink(self):
        for rec in self:
            if rec.state not in  ('draft', 'cancel'):
                raise Warning(
                    _('Vous ne pouvez pas supprimer un formulaire validé'))
        return super(MissionInterne, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'mission.interne') or _('Nouveau')
        res = super(MissionInterne, self).create(vals)
        return res

    @api.onchange('date_retour', 'date_cr')
    def onchange_date_retour_covid(self):
        for rec in self:
            if rec.date_retour and rec.date_cr and rec.date_retour < rec.date_cr:
                raise Warning(_('La date "Test Covid" doit être avant la date d\'arrivée'))
            else:
                pass

    @api.onchange('date_depart', 'date_cd')
    def onchange_date_depart_covid(self):
        for rec in self:
            if rec.date_depart and rec.date_cd and rec.date_depart < rec.date_cd:
                raise Warning(_('La date "Test Covid" doit être avant la date de départ'))
            else:
                pass

    def action_depart(self):
        for rec in self:
            rec.state = 'depart'

    def action_retour(self):
        for rec in self:
            rec.state = 'retour'

    def action_terminer(self):
        for rec in self:
            rec.state = 'terminer'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'


class MissionOrdinaire(models.Model):
    _name = 'mission.ordinaire'
    _description = 'Mission Ordinaire'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Service Number', copy=False, default="Nouveau")
    date = fields.Date(
        string='Date',
        default=fields.Date.today(),
        required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employée',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1),
                                  required=True, copy=True)
    date_depart = fields.Date(
        string='Date de départ', default=fields.Date.context_today, store=True, required=False)
    date_exp = fields.Date(string='Date d\'expiration', required=False)

    date_retour = fields.Date(
        string='Date de Retour', default=fields.Date.context_today, store=True, required=False)

    passport = fields.Char(string='Passeport/CIN', required=False)
    objet = fields.Text(string="Objet Mission", required=False)
    o_mission = fields.Selection(string='Ordre de mission', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )

    date_mission = fields.Date(
        string='Date de mission',
        required=False)
    p_carburant = fields.Selection(string='Carburant', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )

    date_p_carburant = fields.Date(
        string='Date',
        required=False)

    vehicule = fields.Selection(string='Besoin de véhicule ?', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    n_chauffeur = fields.Char(string='Nom du Chauffeur', required=False)
    chauffeur_cont = fields.Char(string='Contact du Chauffeur', required=False)
    matricule = fields.Char(string='Matricule du Véhicule', required=False)
    duree_b = fields.Integer(string='Durée d\'util. du Véhi.', required=False)
    responsable = fields.Char(string='Nom du Responsable', required=False)
    post = fields.Char(string='Poste du responsable', required=False)
    frais_m = fields.Selection(string='Frais de Mission', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_f = fields.Date(string='Date de frais de mission', required=False)
    p_financier = fields.Selection(string='Point financier?', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_pf = fields.Date(string='Date point financier', required=False)

    equipement = fields.Selection(string='Equipement?', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_q = fields.Date(string='Date Equipement', required=False)
    date_eq = fields.Date(string='Date frais Equipement', required=False)

    p_equipement = fields.Selection(string='Point Equipement?', selection=[
        ('oui', 'Oui'), ('non', 'Non')], required=False, )
    date_p_eq = fields.Date(string='Date point Equipement', required=False)

    commentaire_dep = fields.Text(
        string="Commentaire",
        required=False)
    commentaire_ret = fields.Text(string="Commentaire", required=False)
    unity_duree_vehicule = fields.Selection([('jours', 'jours'),
                                             ('semaines', 'semaines'),
                                             ('mois', 'mois'),
                                             ('année', 'années')],
                                            required=False, default='jours')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'mission.ordinaire') or _('Nouveau')
        res = super(MissionOrdinaire, self).create(vals)
        return res

    state = fields.Selection([
        ('draft', 'Nouveau'),
        ('depart', 'Départ'),
        ('retour', 'Retour'),
        ('terminer', 'Terminer'),
        ('cancel', 'Annuler')],
        default='draft',
        track_visibility='onchange', )

    def unlink(self):
        for rec in self:
            if rec.state not in  ('draft', 'cancel'):
                raise Warning(
                    _('Vous ne pouvez pas supprimer un formulaire valider'))
        return super(MissionOrdinaire, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'mission.ordinaire') or _('Nouveau')
        res = super(MissionOrdinaire, self).create(vals)
        return res

    def action_depart(self):
        for rec in self:
            rec.state = 'depart'

    def action_retour(self):
        for rec in self:
            rec.state = 'retour'

    def action_terminer(self):
        for rec in self:
            rec.state = 'terminer'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'


class ReportingTicket(models.Model):
    _name = 'reporting.ticket'
    _description = 'reporting ticket'
    _rec_name = 'name'
    _order = 'name ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True,
                       default=lambda self: _('New'), copy=False)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    employee_id = fields.Many2one('hr.employee', string='Employée',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1),
                                  required=True, copy=True)

    date_v = fields.Date(string='Date de Voyage', store=True, required=False)
    date_r = fields.Date(string='Date retour', required=False)
    trajet = fields.Char(string='Trajet', Required=False)
    nature = fields.Char(string='Nature', required=False)
    montant_b = fields.Float(string='Montant Billet', digits=(12, 2))
    montant_bm = fields.Float(string='Montant Billet modifié', digits=(12, 2))
    montant_bmt = fields.Float(string='Montant Billet modifié (Trajet)', digits=(12, 2))

    montant_total = fields.Float(compute='_compute_montant_total', string='Montant total', digits=(12, 2))
    state = fields.Selection([('draft', 'Nouveau'),
                              ('valider', 'Validé')],
                             default='draft',
                             track_visibility='onchange', )

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(
                    _('Vous ne pouvez pas supprimer un formulaire validé'))
        return super(ReportingTicket, self).unlink()

    def valider(self):
        for rec in self:
            rec.state = 'valider'

    @api.depends('montant_b', 'montant_bm', 'montant_bmt')
    def _compute_montant_total(self):
        for record in self:
            montant_total = 0.0
            montant_b = record.montant_b
            montant_bm = record.montant_bm
            montant_bmt = record.montant_bmt
            record.update({
                'montant_total': record.currency_id.round(montant_b) + record.currency_id.round(
                    montant_bm) + record.currency_id.round(montant_bmt)
            })

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'reporting.ticket') or _('Nouveau')
        res = super(ReportingTicket, self).create(vals)
        return res
