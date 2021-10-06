# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from collections import OrderedDict
from operator import itemgetter
from odoo.addons.portal.controllers.web import Home
from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import groupby as groupbyelem

from odoo.osv.expression import OR


class InheritHome(Home):
    def _login_redirect(self, uid, redirect=None):
        """ Redirect regular users (employees) to the backend) and others to
        the frontend
        """
        if not redirect and request.params.get('login_success'):
            if request.env['res.users'].browse(uid).has_group('base.group_user'):
                redirect = b'/web?' + request.httprequest.query_string
            else:
                redirect = '/my/tasks'
        return super(InheritHome, self)._login_redirect(uid, redirect=redirect)

    # @http.route('/', type='http', auth="public", website=True, sitemap=True)
    # def new_homepage(self):
    #     return request.render('e_formulaire.new_homepage', {})


class InheritCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'project_count' in counters:
            values['project_count'] = request.env['project.project'].search_count([])
        if 'task_count' in counters:
            values['task_count'] = request.env['project.task'].search_count([])
        return values

    # ------------------------------------------------------------
    # My Project
    # ------------------------------------------------------------
    def _project_get_page_view_values(self, project, access_token, **kwargs):
        values = {
            'page_name': 'project',
            'project': project,
        }
        return self._get_page_view_values(project, access_token, values, 'my_projects_history', False, **kwargs)

    @http.route(['/my/formulaire-types', '/my/formulaire-types/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_projects(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Project = request.env['project.project']
        domain = []

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # projects count
        project_count = Project.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/formulaire-types",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=project_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        projects = Project.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_projects_history'] = projects.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'projects': projects,
            'page_name': 'project',
            'default_url': '/my/formulaire-types',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("e_formulaire.portal_my_projects", values)

    @http.route(['/my/formulaire/<int:project_id>'], type='http', auth="public", website=True)
    def portal_my_project(self, project_id=None, access_token=None, **kw):
        try:
            project_sudo = self._document_check_access('project.project', project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._project_get_page_view_values(project_sudo, access_token, **kw)
        return request.render("e_formulaire.portal_my_project", values)

        # ------------------------------------------------------------
        # My Task
        # ------------------------------------------------------------

    def _task_get_page_view_values(self, task, access_token, **kwargs):
        values = {
            'page_name': 'task',
            'task': task,
            'user': request.env.user
        }
        return self._get_page_view_values(task, access_token, values, 'my_tasks_history', False, **kwargs)

    @http.route(['/my/tasks', '/my/tasks/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tasks(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None,
                        search_in='content', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('partner_id', '=', partner.id)]},
        }

        # extends filterby criteria with project the customer has access to
        projects = request.env['project.project'].search([])
        for project in projects:
            searchbar_filters.update({
                str(project.id): {'label': project.name, 'domain': [('project_id', '=', project.id)]}
            })

        # extends filterby criteria with project (criteria name is the project id)
        # Note: portal users can't view projects they don't follow
        project_groups = request.env['project.task'].read_group([('project_id', 'not in', projects.ids)],
                                                                ['project_id'], ['project_id'])
        for group in project_groups:
            proj_id = group['project_id'][0] if group['project_id'] else False
            proj_name = group['project_id'][1] if group['project_id'] else _(
                'Others')
            searchbar_filters.update({
                str(proj_id): {'label': proj_name, 'domain': [('project_id', '=', proj_id)]}
            })

        # # task count
        task_count = request.env['project.task'].search_count([('partner_id', '=', partner.id)])
        # # pager
        pager = request.website.pager(
            url="/my/tasks",
            url_args={'date_begin': date_begin,
                      'date_end': date_end, 'sortby': sortby, },
            total=task_count,
            page=page,
            step=self._items_per_page
        )

        #     order = "stage_id, %s" % order  # force sort on stage first to group by stage in view
        domain = [('partner_id', '=', partner.id)]
        tasks = request.env['project.task'].search(domain,  # order=order,
                                                   limit=self._items_per_page,
                                                   offset=pager['offset'])
        request.session['my_tasks_history'] = tasks.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_tasks': tasks,
            'page_name': 'task',
            'default_url': '/my/tasks',
            'pager': pager,
        })

        return request.render("project.portal_my_tasks", values)

    @http.route(['/my/task/<int:task_id>'], type='http', auth="public", website=True)
    def portal_my_task(self, task_id, access_token=None, report_type=None, download=False, **kw):
        try:
            task_sudo = self._document_check_access(
                'project.task', task_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my/tasks')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=task_sudo, report_type=report_type, report_ref='e_formulaire.dii_attestation_pdf_report', download=download)

        values = self._task_get_page_view_values(task_sudo, access_token, **kw)


        return request.render("project.portal_my_task", values)

    # ___________________________________________________
    # Obtenir un compte

    @http.route(['/obtenir-un-compte'], type='http', auth="public", website=True)
    def nos_services(self):
        return request.render('e_formulaire.o_formulaire_obtenir_un_compte', {})

    # Demande de carte d'importateur DGC
    @http.route(['/formulaire/demande-carte-importateur'], type='http', auth="user", website=True)
    def demande_carte_importateur(self):
        return request.render("e_formulaire.attestation_tenant_lieu_carte_importateur_dgc", {
            'countries': request.env['res.country'].sudo().search([]),
        })

    # Demande d'installation industrielle DII
    @http.route(['/formulaire/demande-autorisation-installation-industrielle'], type='http', auth="user", website=True)
    def demande_installation_industrielle(self):

        return request.render("e_formulaire.demande_autorisation_installationindustrielle_dii", {})

    # Demande d'autorisation de prorogation de succursale DPS
    @http.route(['/formulaire/Demande-autorisation-prorogation-succursale'], type='http', auth="user", website=True)
    def demande_autorisation_prorogation_succursale(self):

        return request.render("e_formulaire.demande_autorisation_prorogation_succursale_dps", {})

    # Attestation tenant lieu de carte d'importateur ATLI
    @http.route(['/formulaire/attestation-tenant-lieu-carte-importateur'], type='http', auth="user", website=True)
    def attestation_tenant_lieu_carte_importateur(self, **kw):

        return request.render("e_formulaire.attestation_tenant_lieu_carte_importateur_atli", {})

    @http.route(['/demande/website_submitted'], type='http', auth="user", methods=['POST'], website=True)
    def demande_submitted(self, **post):
        partner = request.env.user.partner_id

        values = {
            'partner_id': partner.id,
            'name': post.get('name'),
            'raison_sociale': post.get('entreprise'),
            'ifu': post.get('IFU'),
            'rccm': post.get('rccm'),
            'project_id': post.get('Type_formulaire'),
            'produit': post.get('produit'),
            'provenance': post.get('provenance'),
            'montant': post.get('montant'),
            'gerant': post.get('gerant'),
            'date_naissance': post.get('date_naissance'),
            'lieu_naissance': post.get('lieu_naissance'),
            'nationalie_gerant': post.get('nationalie_gerant'),
            "attachment_ids": False,
            'description': post.get('description'),
        }
        partner_id = request.env['res.partner'].sudo().search(
            [('name', '=', post.get('entreprise'))])
        if partner_id:
            values.update({
                'partner_id': partner_id.id,
            })
        project_id = request.env['project.project'].sudo().search([('custome_code', '=', post.get('project_code'))], limit=1)
        if project_id:
            values.update({
                'project_id': project_id.id,
            })
        demande_id = request.env['project.task'].sudo().create(values)
        local_context = http.request.env.context.copy()
        local_context.update({
            'raison_sociale': post.get('entreprise'),
            'ifu': post.get('IFU'),
            'rccm': post.get('rccm'),
            'subject': demande_id.name,
            'number': demande_id.number,
        })

        if post.get("attachment"):
            for files in request.httprequest.files.getlist("attachment"):
                data = files.read()
                if files.filename:
                    request.env["ir.attachment"].sudo().create({
                        "name": files.filename,
                        "datas": base64.b64encode(data),
                        "res_model": "project.task",
                        "res_id": demande_id.id
                    })

        values = {
            'order': demande_id
        }

        return request.render('e_formulaire.website_thanks', values)