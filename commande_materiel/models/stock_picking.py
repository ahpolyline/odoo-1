# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    commande_id = fields.Many2one('commande.materiel', string='Expression des Besoins', readonly=True, copy=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    commande_line_id = fields.Many2one('commande.materiel.line', string='Ligne des commancdes', copy=True)