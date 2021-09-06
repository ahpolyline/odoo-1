from odoo import fields, models, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    form_type1_ids = fields.Many2many('project.project', 'employee1_form_type_rel', 'emp1_id', 'form1_type_id', string='Tags')
    form_type2_ids = fields.Many2many('project.project', 'employee2_form_type_rel', 'emp2_id', 'form2_type_id', string='Tags')
