# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

# To use this wizard just add :
#             view = self.env.ref('be_furmulaire.be_message_wizard')
#             view_id = view and view.id or False
#             context = dict(self._context or {})
#             context['message'] = "Demande confirmée avec Succées"
#             return {
#                 'name': 'Confirmation',
#                 'type': 'ir.actions.act_window',
#                 'view_type': 'form',
#                 'view_mode': 'form',
#                 'res_model': 'be.message.wizard',
#                 'views': [(view.id, 'form')],
#                 'view_id': view.id,
#                 'target': 'new',
#                 'context': context,
#             }

from odoo import api, fields, models


class BeMessageWizard(models.TransientModel):
    _name = 'be.message.wizard'
    _description = 'Missage wizart display a message, alert, success'

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    name = fields.Text(string="Message", readonly=True, default=get_default)
