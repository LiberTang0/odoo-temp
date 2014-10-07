__author__ = 'colin'

from openerp.tests import common
import openerp.modules.registry
import os.path
import openerp.addons.phantomjs_pdf

class TestPrinting(common.SingleTransactionCase):

    def setUp(self):
        super(TestPrinting, self).setUp()
        self.uid = 1
        self.host = 'http://localhost:8169'

    def test_printing(self):
        cr, uid = self.cr, self.uid
        phantomjs = self.registry['phantomjs.pdf']
        output = '/tmp/phantom_test.pdf'

        phantom_data = {
            'url': 'http://localhost:8169/phantomjs',
            'fname': output,
            'database': 't4clinical_test'
        }

        result = phantomjs.phantomjs_print(cr, uid, options=phantom_data, context=None)

        self.assertEqual(result, 'Report printed but not saved in database', 'Error printing and not saving to database')

        self.assertTrue(os.path.isfile(output), 'File is not present')



