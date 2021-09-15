# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    form_type1_ids = fields.Many2many('project.project', 'employee1_form_type_rel', 'emp1_id', 'form1_type_id', string='Tags')
    form_type2_ids = fields.Many2many('project.project', 'employee2_form_type_rel', 'emp2_id', 'form2_type_id', string='Tags')
   # assigne_to1 = fields.One2many('project.task', 'assign_to1', string='Assigne Niveau 1', copy=True, auto_join=True)
   # assigne_to2 = fields.One2many('project.task', 'assign_to2', sring='Assigne Niveau 2', copy=True, auto_join=True)
