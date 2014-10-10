# -*- encoding: utf-8 -*-
{
    'name': 'NH eObs',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': '',
    'description': """    """,
    'author': 'Neova Health',
    'website': 'http://www.neovahealth.co.uk/',
    'depends': ['nh_ews', 'nh_gcs', 'nh_pbp', 'nh_stools', 'nh_graphs', 'phantomjs_pdf'],
    'data': ['wizard/responsibility_allocation_wizard.xml',
             'wizard/cancel_notifications_view.xml',
             'views/wardboard_view.xml',
             'views/workload_view.xml',
             'views/placement_view.xml',
             'views/userboard_view.xml',
             'views/overdue_view.xml',
             'views/views.xml',
             'views/menuitem.xml',
             'views/report_template.xml',
             'security/ir.model.access.csv'],
    'qweb': ['static/src/xml/nh_eobs.xml'],
    'application': True,
    'installable': True,
    'active': False,
}