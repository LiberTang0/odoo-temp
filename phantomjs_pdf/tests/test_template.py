__author__ = 'colin'

from openerp.tests import common
import openerp.modules.registry
from BeautifulSoup import BeautifulSoup

EXAMPLE_HTML = """
<!DOCTYPE html>
<html>
    <head>
        <meta content="text/html; charset=utf-8" http-equiv="content-type"/>
        <title>Example report for {user}</title>
        <link href="/phantomjs/src/css/style.css" rel="stylesheet"/>
    </head>
    <body>
        <div class="full-page page">
            <div class="row">
                <div class="h-big-ratio left">
                    <h2>{user}</h2>
                </div>
                <div class="h-small-ratio">
                    <img style="height: 40px;" class="right" src="data:image/png;base64,{company_logo}"/>
                </div>
            </div>
            <div class="row">
                <h1>Apple Stock Over Time</h1>
                <div id="chart"></div>
                <h1>Table</h1>
                <div>
                    <table class="striped">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody id="table"></tbody>
                    </table>
                </div>
                <script src="/phantomjs/src/js/jquery.js"></script>
                <script src="/phantomjs/src/js/d3.js"></script>
                <script src="/phantomjs/src/js/draw_graph.js"></script>
            </div>
        </div>
    </body>
</html>
"""


class TestTemplate(common.SingleTransactionCase):

    def setUp(self):
        super(TestTemplate, self).setUp()
        self.registry = openerp.modules.registry.RegistryManager.get('t4clinical_test')
        self.uid = 1
        self.host = 'http://localhost:8169'

    def test_templated(self):
        cr, uid = self.cr, self.uid

        company_pool = self.registry['res.company']
        partner_pool = self.registry['res.partner']
        company_logo = partner_pool.read(cr, uid, 1, ['image'], context=None)['image']

        view_obj = self.registry("ir.ui.view")
        rendered_html = view_obj.render(
            cr, uid, 'phantomjs_pdf.base', {'user': 'test', 'company_logo': company_logo}, context=None)


        example_html = EXAMPLE_HTML.format(user='test', company_logo=company_logo)

        rendered_bs = str(BeautifulSoup(rendered_html)).replace('\n', '')
        example_bs = str(BeautifulSoup(example_html)).replace('\n', '')

        # Assert that shit
        self.assertEqual(rendered_bs,
                         example_bs,
                         'DOM from Controller ain\'t the same as DOM from example')
