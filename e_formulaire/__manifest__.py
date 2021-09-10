# -*- coding: utf-8 -*-
{
    'name': "E-Formulaire",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['project',
                'hr',
                'website',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'data/e_formulaire_data.xml',
        'data/email_template.xml',
        'views/report_layout.xml',
        'report/e_demande_report.xml',

        #'views/form_assets.xml',
        'views/e_formulaire_template.xml',
        'views/e_demandes_view.xml',
        'views/e_formulaire_view.xml',
        'views/res_partner_view.xml',

        'views/hr_employee_view.xml',
        'views/res_partner_view.xml',
        'views/e_stages_view.xml',
        'views/res_config_settings_views.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    #'post_init_hook': 'load_translations',
}
