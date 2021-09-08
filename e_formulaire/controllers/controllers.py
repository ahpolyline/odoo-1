# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from collections import OrderedDict
from operator import itemgetter

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import groupby as groupbyelem

from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self):
        values = super(CustomerPortal, self)._prepare_home_portal_values()
        partner = request.env.user.partner_id
        project_count = request.env['project.project'].sudo().search_count([])
        task_count = request.env['project.task'].sudo().search_count([('partner_id','=', partner.id)])
        values.update({
            'project_count': project_count,
            'task_count': task_count,
        })

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

    @http.route(['/nos-services'], type='http', auth="user", website=True)
    def nos_services(self):
        return request.render('e_formulaire.e_formulair_nos_service', {})

    @http.route(['/add/demande-autorisation-installationindustrielle'], type='http', auth="user", website=True)
    def show_formulaure1(self):

        return request.render("e_formulaire.demande_autorisation_installationindustrielle", {})

    @http.route(['/demande/website_submitted'], type='http', auth="user", methods=['POST'], website=True)
    def demande_submitted(self, **post):
        partner = request.env.user.partner_id

        vals = {
            'partner_id': partner.id,
            'name': post.get('name'),
            'raison_sociale': post.get('entreprise'),
            'ifu': post.get('IFU'),
            'rccm': post.get('rccm'),
            'project_id': post.get('Type_formulaire'),
            "attachment_ids": False,
            'description': post.get('description'),
        }
        partner_id = request.env['res.partner'].sudo().search([('name', '=', post.get('entreprise'))])
        if partner_id:
             vals.update({
                 'partner_id': partner_id.id,
             })
        project_id = request.env['project.project'].sudo().search([('custome_code', '=', post.get('project_code'))], limit=1)
        if project_id:
            vals.update({
                'project_id': project_id.id,
            })
        demande_id = request.env['project.task'].sudo().create(vals)
        local_context = http.request.env.context.copy()
        local_context.update({
            'raison_sociale': post.get('entreprise'),
            'ifu': post.get('IFU'),
            'rccm': post.get('rccm'),
            #'date_request': datetime.today(),
            'subject': demande_id.name,
            # 'job_number': workorder_id.job_number,
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

    @http.route(['/my/projects', '/my/projects/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_projects(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Project = request.env['project.project']
        domain1 = []

        if date_begin and date_end:
            domain1 += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        project_count = Project.search_count(domain1)
        pager = request.website.pager(
            url="/my/projects",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=project_count,
            page=page,
            step=self._items_per_page
        )

        domain = [('partner_id', '=', partner.id)]
        job_order_ids = Project.search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'sortby': sortby,
            'job_orders': job_order_ids,
            'page_name': 'project',
            'default_url': '/my/projects',
            'pager': pager
        })
        return request.render("project.portal_my_projects", values)

    @http.route(['/my/tasks', '/my/tasks/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tasks(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None,
                        search_in='content', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        searchbar_filters = {
            'all': {'label': _('Demande d\'autorisation d\'installation industrielle'), 'domain': []},
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
            proj_name = group['project_id'][1] if group['project_id'] else _('Others')
            searchbar_filters.update({
                str(proj_id): {'label': proj_name, 'domain': [('project_id', '=', proj_id)]}
            })

        # # task count
        task_count = request.env['project.task'].search_count([('partner_id','=', partner.id)])
        # # pager
        pager = request.website.pager(
            url="/my/tasks",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, },
            total=task_count,
            page=page,
            step=self._items_per_page
        )

        #     order = "stage_id, %s" % order  # force sort on stage first to group by stage in view
        domain = [('partner_id', '=', partner.id)]
        tasks = request.env['project.task'].search(domain, # order=order,
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
    def portal_my_task(self, task_id, access_token=None, **kw):
        try:
            task_sudo = self._document_check_access('project.task', task_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # ensure attachment are accessible with access token inside template
        for attachment in task_sudo.attachment_ids:
            attachment.generate_access_token()
        values = self._task_get_page_view_values(task_sudo, access_token, **kw)
        return request.render("project.portal_my_task", values)
