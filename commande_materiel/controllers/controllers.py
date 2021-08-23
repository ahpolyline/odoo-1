# -*- coding: utf-8 -*-
# from odoo import http


# class CommandeMateriel(http.Controller):
#     @http.route('/commande_materiel/commande_materiel/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/commande_materiel/commande_materiel/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('commande_materiel.listing', {
#             'root': '/commande_materiel/commande_materiel',
#             'objects': http.request.env['commande_materiel.commande_materiel'].search([]),
#         })

#     @http.route('/commande_materiel/commande_materiel/objects/<model("commande_materiel.commande_materiel"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('commande_materiel.object', {
#             'object': obj
#         })
