# -*- coding: utf-8 -*-
#from odoo import http


# class BeMission(http.Controller):
#     @http.route('/be_mission/be_mission/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/be_mission/be_mission/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('be_mission.listing', {
#             'root': '/be_mission/be_mission',
#             'objects': http.request.env['be_mission.be_mission'].search([]),
#         })

#     @http.route('/be_mission/be_mission/objects/<model("be_mission.be_mission"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('be_mission.object', {
#             'object': obj
#         })
