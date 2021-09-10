# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

_TASK_STATE = [
    ("draft", "Nouveau"),
    ("encour_1", "En Cours Niveau 1"),
    ("encour_2", "En Cours Niveau 2"),
    ("suspendu", 'Suspendu'),
    ("revoque", "Révoqué"),
    ("a_approuver", "A Approuver"),
    ("approuver", "Approuver"),
    ("cancelled", "Cancelled"),
]


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    case_default = fields.Boolean(string="Default for New Projects", help="Si coché le stage va etre statu d'ouverture.",)
    state = fields.Selection(_TASK_STATE)
