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






