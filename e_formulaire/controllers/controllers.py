# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, route, Controller
from odoo.addons.portal.controllers.portal import CustomerPortal as website_account


class NosServices(website_account):

    @http.route(['/nos-services'], type='http', auth="user", website=True)
    def nos_services(self):
        return request.render('e_formulaire.e_formulair_nos_service', {})

    @http.route(['/installation_industrielle'], type='http', auth="user", website=True)
    def partner_form(self, page=1, redirerct=None, **post):
        return request.render('e_formulaire.e_formulaire_installation_industrielle', {})

        #return request.render("'e_formulaire.e_formulaire_installation_industrielle", {})

    @http.route(['/installation_industrielle/submit'], type='http', auth="user", website=True)
    def customer_form_submit(self, **post):
        partner = request.env['res.partner'].create({
            'name': post.get('name'),
            'email': post.get('email'),
            'phone': post.get('phone')
        })
        vals = {
            'partner': partner,
        }
        return request.render("e_formulaire.tmp_formulaire_creer_success", vals)

    @route(['/my/installation_industrielle'], type='http', auth='user', website=True)
    def list_des_demande(self, redirect=None, **post):
        demain = []
        values = {}
        methods = 'new'
        if request.httprequest.method == 'POST':
            start_date = post['start_date']
            end_date = post['end_date']
            status = post['status']
            domain = [
                ('date_approbation', '>=', start_date),
                ('date_approbation', '<=', end_date)
            ]
            if status != 'all':
                domain += [('state', '=', status)]
            commandes = request.env['e.formulaire'].sudo().search(domain)
            request.session.od_count = len(commandes)
            values.update({
                'commandes': commandes,
                'methods': methods,
                'start_date': start_date,
                'end_date': end_date,
                'status': status
            })

            return request.render('e_formulaire.list_des_demande', values)
        return request.render('e_formulaire.list_des_demande')

    @route(['''/my/installation_industrielle/<int:number>'''
            ], type='http', auth="user", website=True)
    def sale_order_view(self, number=None, **post):
        values = {}
        ref = request.env['e.formulaire'].sudo().browse([number])
        return request.render('e_formulaire.list_des_demande_view', {'ref': ref})


    # @http.route(['/installation_industrielle'], type='http', auth="user", website=True)
    # def demande_carte_immatriculation(self, page=1, redirerct=None, **kw):
    #     domain = []
    #     values = {}
    #     methods = 'new'
    #     if request.httprequest.method == 'POST':
    #         start_date = post['start_date']
    #         end_nate = post['end_date']
    #         status = post['status']
    #         domain = [('date_order', '>=', start_date),
    #                   ('date_order', '<=', end_nate)]
    #         if status != 'all':
    #             domain += [('state', '=', status)]
    #         orders = request.env['e.formulaire'].sudo().search(domain)
    #         request.session.od_count = len(orders)
    #         values.update({
    #
    #             'orders': orders,
    #             'methods': methods,
    #             'start_date': start_date,
    #             'end_nate': end_nate,
    #             'status': status
    #
    #         })
    #
    #         return request.render('e_formulaire.e_formulaire_installation_industrielle', values)
    #
    #     return request.render('e_formulaire.e_formulaire_installation_industrielle', {})
