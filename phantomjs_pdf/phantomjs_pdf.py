__author__ = 'colin'
import subprocess, time
from openerp.osv import osv
from datetime import datetime
from openerp.modules.module import get_module_path


class PhantomJSPDF(osv.AbstractModel):

    _name = 'phantomjs.pdf'
    js_file_to_use = get_module_path('phantomjs_pdf') + '/static/js/phantomjs_print.js'

    def phantomjs_print(self, cr, uid, options={}, context=None):
        users_pool = self.pool['res.users']
        user_info = users_pool.read(cr, uid, uid, ['name', 'login', 'password'])
        user_name = user_info['name']
        auth_details = user_info['login']  #'{0}:{1}'.format(user_info['login'], user_info['password']).encode('base64')
        save_to_database = False
        database = options['database']

        # Read options
        url = options['url']
        filename = options['fname']
        if 'res_model' and 'res_id' and 'datas_fname' and 'name' and'description' in options:
            model = options['res_model']
            id = options['res_id']
            datas_fname = options['datas_fname']
            name = options['name']
            description = options['description']
            save_to_database = True


            js_file = self.js_file_to_use
            phantom_loc = 'phantomjs'
        try:
            printed = subprocess.check_output([phantom_loc,
                                               js_file,
                                               url+'&user={0}'.format(user_name), auth_details, database,  filename])
        except OSError:
            return "Phantom JS not found"
        except subprocess.CalledProcessError, e:
            return e.output        
    
        print "JS would have run and printed by now in {0}".format(printed)
        print_result = eval(printed)

        print print_result['file_name']
        printed = print_result['file_name']
        for error in print_result['errors']:
            print "{0}".format(error['message'])

        # do an eval on the returned dictionary


        if printed and len(print_result['errors']) < 1 and save_to_database:
            encoded_pdf = open(printed.rstrip(), "rb").read().encode("base64")
            ir_attachment_pool = self.pool['ir.attachment']
            existing_attachments = ir_attachment_pool.search(cr, uid,
                                                             [['res_model', '=', model],
                                                              ['res_id', '=', id]], context=context)

            for e in existing_attachments:
                print "attachment id is {0} and visit id is {1}".format(e, id)
            values = {
                'name': name,
                'datas_fname': datas_fname,
                'description': description,
                'res_model': model,
                'res_id': id,
                'type': 'binary',
                'datas': encoded_pdf,
                }
            i = 1
            attachment_id = existing_attachments and existing_attachments[0] or None
            cr.commit()

            while i < 5:
                try:
                    if not attachment_id:
                        attachment_id = ir_attachment_pool.create(cr, uid, values, context=context)
                    else:
                        ir_attachment_pool.write(cr, uid, attachment_id, values, context=context)
                    #print "updating existing attachment - {0}".format(attachment_id)
                except Exception as e:
                    print "Exception inc %s" % i
                    cr.rollback()
                    time.sleep(i)
                    i += 1
                else:
                    cr.commit()
                    break
            return attachment_id, context
        elif not save_to_database:
            return "Report printed but not saved in database"
        else:
            if printed:
                return "Report printed with Errors: {0}".format(print_result['errors'])
            else:
                return "Error printing report: {0}".format(print_result['errors'])
