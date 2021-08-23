# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VoyageVacance(models.Model):
    _name = 'voyage.vacance'
    _description = 'vaoyage vacance'
    _rec_name = 'name'
    _order = 'name ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(
                    _('Vous ne pouvez pas supprimer un formulaire valider'))
        return super(VoyageVacance, self).unlink()

    name = fields.Char(string='Name', required=True,
                       default=lambda self: _('New'), copy=False)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    employee_id = fields.Many2one('hr.employee', string='Employée',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1),
                                  required=True, copy=True)
    beneficiaire = fields.Char(
        string='Bénéficiaire',
        required=False)
    date_a = fields.Date(string='Date d\'aller', store=True, required=False)
    date_r = fields.Date(string='Date retour', required=False)
    test_cr = fields.Selection(string='Test COVID', selection=[(
        'oui', 'Oui'), ('non', 'Non')], required=False, )
    date_cr = fields.Date(string='Date de test covid', required=False)
    trajet = fields.Char(string='Trajet', Required=False)
    nature = fields.Char(string='Nature', required=False)
    montant_b = fields.Float(string='Montant Billet', digits=(12, 2))
    montant_bm = fields.Float(string='Montant Billet modifié', digits=(12, 2))
    montant_bmt = fields.Float(string='Montant Billet modifié (Trajet)', digits=(12, 2))
    autres_frais = fields.Float(string='Autres frais', digits=(12, 2))
    montant_total = fields.Float(compute='_compute_montant_total', string='Montant total', digits=(12, 2))
    state = fields.Selection([('draft', 'Nouveau'),
                              ('valider', 'Valider')],
                             default='draft',
                             track_visibility='onchange', )

    @api.depends('montant_b', 'montant_bm', 'montant_bmt', 'autres_frais')
    def _compute_montant_total(self):
        for record in self:
            montant_total = 0.0
            montant_b = record.montant_b
            montant_bm = record.montant_bm
            montant_bmt = record.montant_bmt
            autres = record.autres_frais
            record.update({
                # 'montant_total': record.currency_id.round(montant_b) + record.currency_id.round(montant_bm) + record.currency_id.round(montant_bmt) + record.currency_id.round(autres)
                'montant_total': record.montant_b + record.montant_bm + record.montant_bmt + record.autres_frais
            })

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'voyage.vacance') or _('Nouveau')
        res = super(VoyageVacance, self).create(vals)
        return res

    def valider(self):
        for rec in self:
            rec.state = 'valider'
