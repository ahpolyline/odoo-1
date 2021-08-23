from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    dest_location_id = fields.Many2one(
        'stock.location',
        string='Lieu de destination',
        groups='hr.group_hr_user'
    )

class HrEmployee(models.Model):
    _inherit = 'hr.department'

    dest_location_id = fields.Many2one(
        'stock.location',
        string='Lieu de destination',
    )