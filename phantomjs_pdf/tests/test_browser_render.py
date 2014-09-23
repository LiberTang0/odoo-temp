__author__ = 'colin'

import openerp.tests

class TestBrowserRender(openerp.tests.HttpCase):

    # test score calculation ajax
    def test_browser_render(self):

        test_code = 'if(d3.version == "3.3.9" && $("#chart").has("svg").length == 1){ console.log("ok"); }else{ console.log("error"); }';

        self.phantom_js('http://localhost:8169/phantomjs', test_code, 'document', login='admin')