# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    case_default = fields.Boolean(
        string="Default for New Projects",
        help="If you check this field, this stage will be proposed by default "
        "on each new project. It will not assign this stage to existing "
        "projects.",
    )
