__author__ = 'colin'

import openerp
from openerp import http
from openerp.modules.module import get_module_path
from datetime import datetime
from openerp.http import request
from openerp.osv import fields

endpoint = '/phantomjs/'

class MobileFrontend(openerp.addons.web.controllers.main.Home):

    def mimeifier(self, type):
        if type == 'css':
            return 'text/css'
        if type == 'js':
            return 'text/javascript'

    @http.route(endpoint + 'src/<type>/<resource>', type='http', auth='none')
    def get_resource(self, type, resource, *args, **kw):
        with open(get_module_path('phantomjs_pdf') + '/static/{type}/{resource}'.format(type=type, resource=resource), 'r') as resource:
            return request.make_response(resource.read(), headers={'Content-Type': self.mimeifier(type)})


    @http.route(endpoint, type='http', auth='user')
    def show_demo(self, *args, **kw):
        cr, uid, context = request.cr, request.session.uid, request.context
        company_pool = request.registry['res.company']
        partner_pool = request.registry['res.partner']
        user_pool = request.registry['res.users']

        user_id = user_pool.search(cr, uid, [('login', '=', request.session['login'])],context=context)[0]
        user = user_pool.read(cr, uid, user_id, ['name'], context=context)['name']
        company_name = company_pool.read(cr, uid, 1, ['name'], context=context)['name']
        company_logo = partner_pool.read(cr, uid, 1, ['image'], context=context)['image']

        time_generated = fields.datetime.context_timestamp(cr, user_id, datetime.now(), context=context)\
            .strftime('%d/%m/%Y %H:%M')

        return request.render('phantomjs_pdf.base', qcontext={'user': user,
                                                                             'company_name': company_name,
                                                                             'company_logo': company_logo,
                                                                             'time_generated': time_generated})

