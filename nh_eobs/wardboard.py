# -*- coding: utf-8 -*-
from openerp.osv import orm, fields, osv
import logging        
_logger = logging.getLogger(__name__)
from openerp.addons.nh_activity.activity import except_if
from openerp import SUPERUSER_ID
import controllers.visit_report as visit_report


class wardboard_swap_beds(orm.TransientModel):
    _name = 'wardboard.swap_beds'
    
    _columns = {
        'patient1_id': fields.many2one('nh.clinical.patient', 'Current Patient'),
        'patient2_id': fields.many2one('nh.clinical.patient', 'Patient To Swap With'),
        'ward_location_id':  fields.many2one('nh.clinical.location', "Ward"),
        'location1_id':  fields.many2one('nh.clinical.location', "Current Patient's Location"),
        'location2_id':  fields.many2one('nh.clinical.location', "Location To Swap With"),
    }
    def do_swap(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0])
        values = {
            'location1_id': data.location1_id.id,
            'location2_id': data.location2_id.id
        }
        api = self.pool['nh.clinical.api']
        api.create_complete(cr, uid, 'nh.clinical.patient.swap_beds', {}, values)
        
    
    def onchange_location2(self, cr, uid, ids, location2_id, context=None):
        if not location2_id:
            return {'value': {'patient2_id': False}}
        api = self.pool['nh.clinical.api']
        patient = api.patient_map(cr, uid, location_ids=[location2_id])
        if not patient:
            return {'value': {'patient2_id': False, 'location2_id': False}}
        return {'value': {'patient2_id': patient.values()[0]['id']}} 

class wardboard_patient_placement(orm.TransientModel):
    _name = "wardboard.patient.placement"
    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
        'ward_location_id':  fields.many2one('nh.clinical.location', "Ward"),
        'bed_src_location_id':  fields.many2one('nh.clinical.location', "Source Bed"),
        'bed_dst_location_id':  fields.many2one('nh.clinical.location', "Destination Bed")
    }
    def do_move(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        api = self.pool['nh.clinical.api']
        move_pool = self.pool['nh.clinical.patient.move']
        activity_pool = self.pool['nh.activity']
        spell_activity_id = api.get_patient_spell_activity_id(cr, uid, wiz.patient_id.id)
        # move to location
        move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,
                                                    {'parent_id': spell_activity_id},
                                                    {'patient_id': wiz.patient_id.id,
                                                     'location_id': wiz.bed_dst_location_id.id})
        activity_pool.complete(cr, uid, move_activity_id)
        activity_pool.submit(cr, uid, spell_activity_id, {'location_id': wiz.bed_dst_location_id.id})


class wardboard_device_session_start(orm.TransientModel):
    _name = "wardboard.device.session.start"
    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
        'device_category_id': fields.many2one('nh.clinical.device.category', 'Device Category'),
        'device_type_id':  fields.many2one('nh.clinical.device.type', "Device Type"),
        'device_id':  fields.many2one('nh.clinical.device', "Device"),
        'location': fields.char('Location', size=50)
    }

    def onchange_device_category_id(self, cr, uid, ids, device_category_id, context=None):
        response = False
        if device_category_id:
            response = {'value': {'device_id': False, 'device_type_id': False}}
            ids = self.pool['nh.clinical.device.type'].search(cr, uid, [('category_id', '=', device_category_id)])
            response.update({'domain': {'device_type_id': [('id', 'in', ids)]}})
        return response

    def onchange_device_type_id(self, cr, uid, ids, device_type_id, context=None):
        response = False
        if device_type_id:
            response = {'value': {'device_id': False}}
            ids = self.pool['nh.clinical.device'].search(cr, uid, [('type_id', '=', device_type_id)])
            response.update({'domain': {'device_id': [('id', 'in', ids), ('is_available', '=', True)]}})
        return response

    def onchange_device_id(self, cr, uid, ids, device_id, context=None):
        device_pool = self.pool['nh.clinical.device']
        if not device_id:
            return {}
        device = device_pool.browse(cr, uid, device_id, context=context)
        return {'value': {'device_type_id': device.type_id.id}}

    def do_start(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        spell_activity_id = self.pool['nh.clinical.api'].get_patient_spell_activity_id(cr, uid, wiz.patient_id.id)
        device_activity_id = self.pool['nh.clinical.device.session'].create_activity(cr, uid,
                                                {'parent_id': spell_activity_id},
                                                {'patient_id': wiz.patient_id.id,
                                                 'device_type_id': wiz.device_type_id.id,
                                                 'device_id': wiz.device_id.id if wiz.device_id else False})
        self.pool['nh.activity'].start(cr, uid, device_activity_id, context)
        self.pool['nh.activity'].submit(cr, uid, device_activity_id, {'location': wiz.location}, context)

class wardboard_device_session_complete(orm.TransientModel):
    _name = "wardboard.device.session.complete"

    _columns = {
        'session_id': fields.many2one('nh.clinical.device.session', 'Session'),
        'removal_reason': fields.char('Removal reason', size=100),
        'planned': fields.selection((('planned', 'Planned'), ('unplanned', 'Unplanned')), 'Planned?')
    }   
    
    def do_complete(self, cr, uid, ids, context=None):
        activity_pool = self.pool['nh.activity']
        wiz = self.browse(cr, uid, ids[0])
        activity_pool.submit(cr, uid, wiz.session_id.activity_id.id, {'removal_reason': wiz.removal_reason, 'planned': wiz.planned}, context)
        activity_pool.complete(cr, uid, wiz.session_id.activity_id.id, context)
        # refreshing view
        spell_activity_id = wiz.session_id.activity_id.parent_id.id
        wardboard_pool = self.pool['nh.clinical.wardboard']
        wardboard_id = wardboard_pool.search(cr, uid, [['spell_activity_id', '=', spell_activity_id]])[0]
        view_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'nh_eobs', 'view_wardboard_form')[1]
        #FIXME should be done more elegantly on client side
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.wardboard',
            'res_id': wardboard_id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'inline',
            'context': context,
            'view_id': view_id
        }


class nh_clinical_device_session(orm.Model):
    _inherit = "nh.clinical.device.session"

    def device_session_complete(self, cr, uid, ids, context=None):
        device_session = self.browse(cr, uid, ids[0], context=context)
        res_id = self.pool['wardboard.device.session.complete'].create(cr, uid, {'session_id': device_session.id})
        view_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'nh_eobs', 'view_wardboard_device_session_complete_form')[1]

        return {
            'name': "Complete Device Session: %s" % device_session.patient_id.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'wardboard.device.session.complete',
            'res_id': res_id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
            'view_id': view_id
        }


class nh_clinical_wardboard(orm.Model):
    _name = "nh.clinical.wardboard"
#     _inherits = {
#                  'nh.clinical.patient': 'patient_id',
#     }
    _description = "Wardboard"
    _auto = False
    _table = "nh_clinical_wardboard"
    _trend_strings = [('up', 'up'), ('down', 'down'), ('same', 'same'), ('none', 'none'), ('one', 'one')]
    _rec_name = 'full_name'

    def _get_logo(self, cr, uid, ids, fields_name, arg, context=None):
        res = {}
        for board in self.browse(cr, uid, ids, context=context):
            res[board.id] = board.patient_id.partner_id.company_id.logo
        return res

    _clinical_risk_selection = [['NoScore', 'No Score Yet'],
                                ['High', 'High Risk'],
                                ['Medium', 'Medium Risk'],
                                ['Low', 'Low Risk'],
                                ['None', 'No Risk']]
    _boolean_selection = [('yes', 'Yes'),
                          ('no', 'No')]
    
    
    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        umap = self.pool['nh.clinical.api'].user_map(cr,user, 
                                                     group_xmlids=['group_nhc_hca', 'group_nhc_nurse',
                                                                   'group_nhc_ward_manager', 'group_nhc_doctor'])
        
        self._columns['o2target'].readonly = not (umap.get(user) and 'group_nhc_doctor' in umap[user]['group_xmlids'])
        res = super(nh_clinical_wardboard, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)    
        return res

    def _get_started_device_session_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = {}.fromkeys(ids, False)
        sql = """select spell_id, ids 
                    from wb_activity_data 
                    where data_model='nh.clinical.device.session' 
                        and state in ('started') and spell_id in (%s)""" % ", ".join([str(spell_id) for spell_id in ids])
        cr.execute(sql)
        res.update({r['spell_id']: r['ids'] for r in cr.dictfetchall()})
        return res 

    def _get_terminated_device_session_ids(self, cr, uid, ids, field_name, arg, context=None):
        res = {}.fromkeys(ids, False)
        sql = """select spell_id, ids 
                    from wb_activity_data 
                    where data_model='nh.clinical.device.session' 
                        and state in ('completed', 'cancelled') and spell_id in (%s)""" % ", ".join([str(spell_id) for spell_id in ids])
        cr.execute(sql)
        res.update({r['spell_id']: r['ids'] for r in cr.dictfetchall()})
        return res    

    def _get_data_ids_multi(self, cr, uid, ids, field_names, arg, context=None):
        res = {id: {field_name: [] for field_name in field_names} for id in ids}
        for field_name in field_names:
            model_name = self._columns[field_name].relation
            sql = """select spell_id, ids from wb_activity_data where data_model='%s' and spell_id in (%s) and state='completed'"""\
                             % (model_name, ", ".join([str(spell_id) for spell_id in ids]))
            cr.execute(sql)
            rows = cr.dictfetchall()
            for row in rows:
                res[row['spell_id']][field_name] = row['ids']
        return res

    def _get_transferred_user_ids(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for wb_id in ids:
            user_ids = self.pool['nh.clinical.spell'].read(cr, uid, wb_id, ['transfered_user_ids'], context=context)['transfered_user_ids']
            res[wb_id] = user_ids
        return res

    def _transferred_user_ids_search(self, cr, uid, obj, name, args, domain=None, context=None):
        arg1, op, arg2 = args[0]
        arg2 = isinstance(arg2, (list, tuple)) and arg2 or [arg2]
        all_ids = self.search(cr, uid, [])
        wb_user_map = self._get_transferred_user_ids(cr, uid, all_ids, 'transferred_user_ids', None)
        wb_ids = [k for k, v in wb_user_map.items() if set(v or []) & set(arg2 or [])]

        return [('id', 'in', wb_ids)]
    
    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=1, ondelete='restrict'),
        'company_logo': fields.function(_get_logo, type='binary', string='Logo'),
        'spell_activity_id': fields.many2one('nh.activity', 'Spell Activity'),
        'spell_date_started': fields.datetime('Spell Start Date'),
        'spell_date_terminated': fields.datetime('Spell Discharge Date'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS'),
        'spell_code': fields.text('Spell Code'),
        'full_name': fields.text("Family Name"),
        'given_name': fields.text("Given Name"),
        'middle_names': fields.text("Middle Names"),
        'family_name': fields.text("Family Name"),
        'location': fields.text("Location"),
        'clinical_risk': fields.selection(_clinical_risk_selection, "Clinical Risk"),
        'ward_id': fields.many2one('nh.clinical.location', 'Ward'),
        'location_id': fields.many2one('nh.clinical.location', "Location"),
        'sex': fields.text("Sex"),
        'dob': fields.datetime("DOB"),
        'hospital_number': fields.text('Hospital Number'),
        'nhs_number': fields.text('NHS Number'),
        'age': fields.integer("Age"),
        'next_diff': fields.text("Time to Next Obs"),
        'frequency': fields.text("Frequency"),
        'ews_score_string': fields.text("Latest Score"),
        'ews_score': fields.integer("Latest Score"),
        'ews_trend_string': fields.selection(_trend_strings, "Score Trend String"),
        'ews_trend': fields.integer("Score Trend"),
        'mrsa': fields.selection(_boolean_selection, "MRSA"),
        'diabetes': fields.selection(_boolean_selection, "Diabetes"),
        'pbp_monitoring': fields.selection(_boolean_selection, "Postural Blood Pressure Monitoring"),
        'weight_monitoring': fields.selection(_boolean_selection, "Weight Monitoring"),
        'height': fields.float("Height"),
        'o2target': fields.many2one('nh.clinical.o2level', 'O2 Target'),
        'consultant_names': fields.text("Consulting Doctors"),
        'terminated_device_session_ids': fields.function(_get_terminated_device_session_ids, type='many2many', relation='nh.clinical.device.session', string='Device Session History'),
        'started_device_session_ids': fields.function(_get_started_device_session_ids, type='many2many', relation='nh.clinical.device.session', string='Started Device Sessions'),
        'spell_ids': fields.function(_get_data_ids_multi, multi='spell_ids', type='many2many', relation='nh.clinical.spell', string='Spells'),
        'move_ids': fields.function(_get_data_ids_multi, multi='move_ids', type='many2many', relation='nh.clinical.patient.move', string='Patient Moves'),
        'o2target_ids': fields.function(_get_data_ids_multi, multi='o2target_ids',type='many2many', relation='nh.clinical.patient.o2target', string='O2 Targets'),
        'weight_ids': fields.function(_get_data_ids_multi, multi='weight_ids',type='many2many', relation='nh.clinical.patient.observation.weight', string='Weight Obs'),
        'blood_sugar_ids': fields.function(_get_data_ids_multi, multi='blood_sugar_ids',type='many2many', relation='nh.clinical.patient.observation.blood_sugar', string='Blood Sugar Obs'),
        'mrsa_ids': fields.function(_get_data_ids_multi, multi='mrsa_ids',type='many2many', relation='nh.clinical.patient.mrsa', string='MRSA'),
        'diabetes_ids': fields.function(_get_data_ids_multi, multi='diabetes_ids',type='many2many', relation='nh.clinical.patient.diabetes', string='Diabetes'),
        'pbp_monitoring_ids': fields.function(_get_data_ids_multi, multi='pbp_monitoring_ids',type='many2many', relation='nh.clinical.patient.pbp_monitoring', string='PBP Monitoring'),
        'weight_monitoring_ids': fields.function(_get_data_ids_multi, multi='weight_monitoring_ids',type='many2many', relation='nh.clinical.patient.weight_monitoring', string='Weight Monitoring'),
        'pbp_ids': fields.function(_get_data_ids_multi, multi='pbp_ids',type='many2many', relation='nh.clinical.patient.observation.pbp', string='PBP Obs'),
        'ews_ids': fields.function(_get_data_ids_multi, multi='ews_ids',type='many2many', relation='nh.clinical.patient.observation.ews', string='EWS Obs'),
        'ews_list_ids': fields.function(_get_data_ids_multi, multi='ews_list_ids',type='many2many', relation='nh.clinical.patient.observation.ews', string='EWS Obs List'),
        'transferred_user_ids': fields.function(_get_transferred_user_ids, type='many2many', relation='res.users', fnct_search=_transferred_user_ids_search, string='Recently Transferred Access')
    }

    def _get_cr_groups(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        res = [['NoScore', 'No Score Yet'], ['High', 'High Risk'], ['Medium', 'Medium Risk'], ['Low', 'Low Risk'], ['None', 'No Risk']]
        fold = {r[0]: False for r in res}
        return res, fold

    _group_by_full = {
        'clinical_risk': _get_cr_groups,
    }
    
    def device_session_start(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)
        res_id = self.pool['wardboard.device.session.start'].create(cr, uid, 
                                                        {
                                                         'patient_id': wardboard.patient_id.id,
                                                         'device_id': None
                                                         })
        view_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'nh_eobs', 'view_wardboard_device_session_start_form')[1]
        return {
            'name': "Start Device Session: %s" % wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'wardboard.device.session.start',
            'res_id': res_id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
            'view_id': view_id
        }


    def wardboard_swap_beds(self, cr, uid, ids, context=None):
        api = self.pool['nh.clinical.api']
        wb = self.browse(cr, uid, ids[0])
        res_id = api.create(cr, uid, 'wardboard.swap_beds', 
                                     {'patient1_id':  wb.patient_id.id,
                                      'location1_id': wb.location_id.id,
                                      'ward_location_id': wb.location_id.parent_id.id})
        view_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'nh_eobs', 'view_wardboard_swap_beds_form')[1]
        return {
            'name': "Swap Beds",
            'type': 'ir.actions.act_window',
            'res_model': 'wardboard.swap_beds',
            'res_id': res_id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
            'view_id': view_id
        }

    
    def wardboard_patient_placement(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)
        # assumed that patient's placement is completed
        # parent location of bed is taken as ward
        except_if(wardboard.location_id.usage != 'bed', msg="Patient must be placed to bed before moving!")
        sql = """
        with 
            recursive route(level, path, parent_id, id) as (
                    select 0, id::text, parent_id, id 
                    from nh_clinical_location 
                    where parent_id is null
                union
                    select level + 1, path||','||location.id, location.parent_id, location.id 
                    from nh_clinical_location location 
                    join route on location.parent_id = route.id
            )
            select 
                route.id as location_id, 
                ('{'||path||'}')::int[] as parent_ids 
            from route
            where id = %s 
            order by path
        """ % wardboard.location_id.id
        cr.execute(sql)
        parent_ids = (cr.dictfetchone() or {}).get('parent_ids')
        ward_location_ids = self.pool['nh.clinical.location'].search(cr, uid, [['id','in',parent_ids], ['usage','=','ward']])
        ward_location_id = ward_location_ids and ward_location_ids[0] or False
        res_id = self.pool['wardboard.patient.placement'].create(cr, uid, 
                                                        {
                                                         'patient_id': wardboard.patient_id.id,
                                                         'ward_location_id': ward_location_id or wardboard.location_id.parent_id.id,
                                                         'bed_src_location_id': wardboard.location_id.id,
                                                         'bed_dst_location_id': None
                                                         })
        view_id = self.pool['ir.model.data'].get_object_reference(cr, uid, 'nh_eobs', 'view_wardboard_patient_placement_form')[1]
        return {
            'name': "Move Patient: %s" % wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'wardboard.patient.placement',
            'res_id': res_id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
            'view_id': view_id
        }

    def wardboard_prescribe(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_wardboard_prescribe_form')], context=context)
        if not model_data_ids:
            pass
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context=context)[0]['res_id']
        return {
            'name': wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.wardboard',
            'res_id': ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': context,
            'view_id': int(view_id)
        }
        
    def wardboard_chart(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_wardboard_chart_form')], context=context)
        if not model_data_ids:
            pass
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context=context)[0]['res_id']
        return {
            'name': wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.wardboard',
            'res_id': ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
            'view_id': int(view_id)
        }

    def wardboard_weight_chart(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_wardboard_weight_chart_form')], context=context)
        if not model_data_ids:
            pass
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context=context)[0]['res_id']

        context.update({'height': wardboard.height})
        return {
            'name': wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.wardboard',
            'res_id': ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
            'view_id': int(view_id)
        }

    def wardboard_bs_chart(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_wardboard_bs_chart_form')], context=context)
        if not model_data_ids:
            pass
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context=context)[0]['res_id']
        return {
            'name': wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.wardboard',
            'res_id': ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
            'view_id': int(view_id)
        }

    def wardboard_ews(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)
        return {
            'name': wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.patient.observation.ews',
            'view_mode': 'tree',
            'view_type': 'tree',
            'domain': [('patient_id', '=', wardboard.patient_id.id), ('state', '=', 'completed')],
            'target': 'new',
            'context': context
        }

    def print_chart(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)

        model_data_pool = self.pool['ir.model.data']
        model_data_ids = model_data_pool.search(cr, uid, [('name', '=', 'view_wardboard_print_chart_form')], context=context)
        if not model_data_ids:
            pass
        view_id = model_data_pool.read(cr, uid, model_data_ids, ['res_id'], context=context)[0]['res_id']
        context.update({'printing': 'true'})
        return {
            'name': wardboard.full_name,
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.wardboard',
            'res_id': ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'inline',
            'context': context,
            'view_id': int(view_id)
        }

    def print_report(self, cr, uid, ids, context=None):
        wardboard = self.browse(cr, uid, ids[0], context=context)
        users = self.pool['res.users']
        config = self.pool['ir.config_parameter']
        base_url = config.read(cr, uid, config.search(cr, uid, [('key', '=', 'web.base.url')]),['value'])[0]['value']
        user = users.read(cr, uid, uid, ['name'])['name']
        # get spell id
        spell_id = wardboard.id
        # Format URL for report
        url = '{base_url}{endpoint}{spell_id}/'.format(base_url=base_url,
                                                       endpoint=visit_report.endpoint,
                                                       spell_id=spell_id)
        # Create filename
        fname = '/tmp/open_eobs/{spell_id}.pdf'.format(spell_id=spell_id)
        # Create options dict
        data_fname = '{hospital_number}_report.pdf'.format(hospital_number=wardboard.hospital_number)
        name = 'Patient Report for {patient_name}'.format(patient_name=wardboard.full_name)
        description = 'Patient Report for {patient_name}'.format(patient_name=wardboard.full_name)
        options = {
            'url': url,
            'fname': fname,
            'res_model': 'nh.clinical.spell',
            'res_id': spell_id,
            'datas_fname': data_fname,
            'name': name,
            'description': description,
            'database': cr.dbname
        }

        # Call the print function
        phantomjs = self.pool['phantomjs.pdf']
        print_result = phantomjs.phantomjs_print(cr, uid, options, context=context)
        if not isinstance(print_result, str):
            return print_result
        else:
            _logger.warn(print_result)
            return False

    def write(self, cr, uid, ids, vals, context=None):
        activity_pool = self.pool['nh.activity']
        for wb in self.browse(cr, uid, ids, context=context):
            if 'mrsa' in vals:
                mrsa_pool = self.pool['nh.clinical.patient.mrsa']
                mrsa_id = mrsa_pool.create_activity(cr, SUPERUSER_ID, {
                    'parent_id': wb.spell_activity_id.id,
                }, {
                    'patient_id': wb.spell_activity_id.patient_id.id,
                    'mrsa': vals['mrsa'] == 'yes'
                }, context=context)
                activity_pool.complete(cr, uid, mrsa_id, context=context)
            if 'diabetes' in vals:
                diabetes_pool = self.pool['nh.clinical.patient.diabetes']
                diabetes_id = diabetes_pool.create_activity(cr, SUPERUSER_ID, {
                    'parent_id': wb.spell_activity_id.id,
                }, {
                    'patient_id': wb.spell_activity_id.patient_id.id,
                    'diabetes': vals['diabetes'] == 'yes'
                }, context=context)
                activity_pool.complete(cr, uid, diabetes_id, context=context)
            if 'pbp_monitoring' in vals:
                pbpm_pool = self.pool['nh.clinical.patient.pbp_monitoring']
                pbpm_id = pbpm_pool.create_activity(cr, SUPERUSER_ID, {
                    'parent_id': wb.spell_activity_id.id,
                }, {
                    'patient_id': wb.spell_activity_id.patient_id.id,
                    'pbp_monitoring': vals['pbp_monitoring'] == 'yes'
                }, context=context)
                activity_pool.complete(cr, uid, pbpm_id, context=context)
            if 'weight_monitoring' in vals:
                wm_pool = self.pool['nh.clinical.patient.weight_monitoring']
                wm_id = wm_pool.create_activity(cr, SUPERUSER_ID, {
                    'parent_id': wb.spell_activity_id.id,
                }, {
                    'patient_id': wb.spell_activity_id.patient_id.id,
                    'weight_monitoring': vals['weight_monitoring'] == 'yes'
                }, context=context)
                activity_pool.complete(cr, uid, wm_id, context=context)
            if 'o2target' in vals:
                o2target_pool = self.pool['nh.clinical.patient.o2target']
                o2target_id = o2target_pool.create_activity(cr, SUPERUSER_ID, {
                    'parent_id': wb.spell_activity_id.id,
                }, {
                    'patient_id': wb.spell_activity_id.patient_id.id,
                    'level_id': vals['o2target']
                }, context=context)
                activity_pool.complete(cr, uid, o2target_id, context=context)
        return True

    def test(self, cr):
        cr.execute("""
            select
                activity.patient_id,
                activity.spell_id,
                activity.state, 
                activity.date_scheduled,
                ews.id,
                ews.score,
                ews.frequency,
                ews.clinical_risk,
                case when activity.date_scheduled < now() at time zone 'UTC' then 'overdue: ' else '' end as next_diff_polarity,
                case activity.date_scheduled is null
                    when false then justify_hours(greatest(now() at time zone 'UTC',activity.date_scheduled) - least(now() at time zone 'UTC', activity.date_scheduled))
                    else interval '0s' 
                end as next_diff_interval,
                activity.rank
            from wb_activity_ranked activity
            inner join nh_clinical_patient_observation_ews ews on activity.data_id = ews.id 
                and activity.data_model = 'nh.clinical.patient.observation.ews'
            """)
        for r in cr.dictfetchall():
            print r        
        
    def test2(self, cr):
        cr.execute("""
    with 
    ews as(
            select 
                activity.patient_id,
                activity.spell_id,
                activity.state, 
                activity.date_scheduled,
                ews.id,
                ews.score,
                ews.frequency,
                ews.clinical_risk,
                case when activity.date_scheduled < now() at time zone 'UTC' then 'overdue: ' else '' end as next_diff_polarity,
                case activity.date_scheduled is null
                    when false then justify_hours(greatest(now() at time zone 'UTC',activity.date_scheduled) - least(now() at time zone 'UTC', activity.date_scheduled))
                    else interval '0s' 
                end as next_diff_interval,
                activity.rank
            from wb_activity_ranked activity
            inner join nh_clinical_patient_observation_ews ews on activity.data_id = ews.id 
                and activity.data_model = 'nh.clinical.patient.observation.ews'
    ),    
    cosulting_doctors as(
            select 
                spell.id as spell_id,
                array_to_string(array_agg(doctor.name), ' / ') as names    
            from nh_clinical_spell spell
            inner join con_doctor_spell_rel on con_doctor_spell_rel.spell_id = spell.id
            inner join res_partner doctor on con_doctor_spell_rel.doctor_id = doctor.id
            group by spell.id
            ),
            
    param as(
    
        select 
            activity.spell_id,
            height.height,
            diabetes.diabetes,
            mrsa.mrsa,
            pbpm.pbp_monitoring,
            wm.weight_monitoring,
            o2target_level.id as o2target_level_id
        from wb_activity_latest activity
        left join nh_clinical_patient_observation_height height on activity.ids && array[height.activity_id]
        left join nh_clinical_patient_diabetes diabetes on activity.ids && array[diabetes.activity_id]
        left join nh_clinical_patient_pbp_monitoring pbpm on activity.ids && array[pbpm.activity_id]
        left join nh_clinical_patient_weight_monitoring wm on activity.ids && array[wm.activity_id]
        left join nh_clinical_patient_o2target o2target on activity.ids && array[o2target.activity_id]
        left join nh_clinical_o2level o2target_level on o2target_level.id = o2target.level_id
        left join nh_clinical_patient_mrsa mrsa on activity.ids && array[mrsa.activity_id]    
        where activity.state = 'completed'
    )
    
    select 
        spell.id as id,
        spell.patient_id as patient_id,
        spell_activity.id as spell_activity_id,
        spell_activity.date_started as spell_date_started,
        spell_activity.date_terminated as spell_date_terminated,
        spell.pos_id,
        spell.code as spell_code,
        patient.family_name,
        patient.given_name,
        patient.middle_names,
        coalesce(patient.family_name, '') || ', ' || coalesce(patient.given_name, '') || ' ' || coalesce(patient.middle_names,'') as full_name,
        location.code as location,
        location.id as location_id,
        location.parent_id as ward_id,
        patient.sex,
        patient.dob,
        patient.other_identifier as hospital_number,
        patient.patient_identifier as nhs_number,
        extract(year from age(now(), patient.dob)) as age,
        ews0.next_diff_polarity ||
        case when extract(days from ews0.next_diff_interval) > 0
            then  extract(days from ews0.next_diff_interval) || ' day(s) ' else ''
        end || to_char(ews0.next_diff_interval, 'HH24:MI') next_diff,
        case ews0.frequency < 60
            when true then ews0.frequency || ' min(s)'
            else ews0.frequency/60 || ' hour(s) ' || ews0.frequency - ews0.frequency/60*60 || ' min(s)'
        end as frequency,
        case when ews1.id is null then 'none' else ews1.score::text end as ews_score_string,    
        ews1.score as ews_score,
        case
            when ews1.id is not null and ews2.id is not null and (ews1.score - ews2.score) = 0 then 'same'
            when ews1.id is not null and ews2.id is not null and (ews1.score - ews2.score) > 0 then 'down'
            when ews1.id is not null and ews2.id is not null and (ews1.score - ews2.score) < 0 then 'up'
            when ews1.id is null and ews2.id is null then 'none'
            when ews1.id is not null and ews2.id is null then 'first'
            when ews1.id is null and ews2.id is not null then 'no latest' -- shouldn't happen. 
        end as ews_trend_string,
        case when ews1.id is null then 'NoScore' else ews1.clinical_risk end as clinical_risk,
        ews1.score - ews2.score as ews_trend,
        param.height,
        param.o2target_level_id as o2target,
        case when param.mrsa then 'yes' else 'no' end as mrsa,
        case when param.diabetes then 'yes' else 'no' end as diabetes,
        case when param.pbp_monitoring then 'yes' else 'no' end as pbp_monitoring,
        case when param.weight_monitoring then 'yes' else 'no' end as weight_monitoring,
        cosulting_doctors.names as consultant_names
        
    from nh_clinical_spell spell
    inner join nh_activity spell_activity on spell_activity.id = spell.activity_id
    inner join nh_clinical_patient patient on spell.patient_id = patient.id
    left join nh_clinical_location location on location.id = spell.location_id
    left join ews ews1 on spell.id = ews1.spell_id and ews1.rank = 1 and ews1.state = 'completed'
    left join ews ews2 on spell.id = ews2.spell_id and ews2.rank = 2 and ews2.state = 'completed'
    left join ews ews0 on spell.id = ews0.spell_id and ews0.rank = 1 and ews0.state = 'scheduled'    
    left join cosulting_doctors on cosulting_doctors.spell_id = spell.id
    inner join param on param.spell_id = spell.id

    where spell_activity.state = 'started' 
""")
        for r in cr.dictfetchall():
            print r  
            
            
            
    def init(self, cr):
        cr.execute("""


drop view if exists nh_clinical_wardboard;
drop view if exists wb_activity_ranked;
drop view if exists wb_activity_latest;
drop view if exists wb_activity_data;
create or replace view 
-- activity per spell, data_model, state
wb_activity_ranked as(
        select 
            spell.id as spell_id,
            activity.*,
            split_part(activity.data_ref, ',', 2)::int as data_id,
            rank() over (partition by spell.id, activity.data_model, activity.state order by activity.sequence desc)
        from nh_clinical_spell spell
        inner join nh_activity activity on activity.spell_activity_id = spell.activity_id
);

create or replace view 
wb_activity_latest as(
    with 
    max_sequence as(
        select 
            spell.id as spell_id,
            activity.data_model,
            activity.state,
            max(activity.sequence) as sequence
        from nh_clinical_spell spell
        inner join nh_activity activity on activity.patient_id = spell.patient_id
        group by spell_id, activity.data_model, activity.state
    )
    select 
        max_sequence.spell_id,
        activity.state,
        array_agg(activity.id) as ids
    from nh_activity activity
    inner join max_sequence on max_sequence.data_model = activity.data_model
         and max_sequence.state = activity.state
         and max_sequence.sequence = activity.sequence
    group by max_sequence.spell_id, activity.state
);

create or replace view 
-- activity data ids per spell/pateint_id, data_model, state
wb_activity_data as(
        select 
            spell.id as spell_id,
            spell.patient_id,
            activity.data_model, 
            activity.state,
            array_agg(split_part(activity.data_ref, ',', 2)::int) as ids
        from nh_clinical_spell spell
        inner join nh_activity activity on activity.patient_id = spell.patient_id
        group by spell_id, spell.patient_id, activity.data_model, activity.state
); 


create or replace view
nh_clinical_wardboard as(
    with 
    ews as(
            select 
                activity.patient_id,
                activity.spell_id,
                activity.state, 
                activity.date_scheduled,
                ews.id,
                ews.score,
                ews.frequency,
                ews.clinical_risk,
                case when activity.date_scheduled < now() at time zone 'UTC' then 'overdue: ' else '' end as next_diff_polarity,
                case activity.date_scheduled is null
                    when false then justify_hours(greatest(now() at time zone 'UTC',activity.date_scheduled) - least(now() at time zone 'UTC', activity.date_scheduled))
                    else interval '0s' 
                end as next_diff_interval,
                activity.rank
            from wb_activity_ranked activity
            inner join nh_clinical_patient_observation_ews ews on activity.data_id = ews.id 
                and activity.data_model = 'nh.clinical.patient.observation.ews'
    ),    
    cosulting_doctors as(
            select 
                spell.id as spell_id,
                array_to_string(array_agg(doctor.name), ' / ') as names    
            from nh_clinical_spell spell
            inner join con_doctor_spell_rel on con_doctor_spell_rel.spell_id = spell.id
            inner join res_partner doctor on con_doctor_spell_rel.doctor_id = doctor.id
            group by spell.id
            ),
            
    param as(
    
        select 
            activity.spell_id,
            height.height,
            diabetes.diabetes,
            mrsa.mrsa,
            pbpm.pbp_monitoring,
            wm.weight_monitoring,
            o2target_level.id as o2target_level_id
        from wb_activity_latest activity
        left join nh_clinical_patient_observation_height height on activity.ids && array[height.activity_id]
        left join nh_clinical_patient_diabetes diabetes on activity.ids && array[diabetes.activity_id]
        left join nh_clinical_patient_pbp_monitoring pbpm on activity.ids && array[pbpm.activity_id]
        left join nh_clinical_patient_weight_monitoring wm on activity.ids && array[wm.activity_id]
        left join nh_clinical_patient_o2target o2target on activity.ids && array[o2target.activity_id]
        left join nh_clinical_o2level o2target_level on o2target_level.id = o2target.level_id
        left join nh_clinical_patient_mrsa mrsa on activity.ids && array[mrsa.activity_id]    
        where activity.state = 'completed'
    )
    
    select 
        spell.id as id,
        spell.patient_id as patient_id,
        spell_activity.id as spell_activity_id,
        spell_activity.date_started as spell_date_started,
        spell_activity.date_terminated as spell_date_terminated,
        spell.pos_id,
        spell.code as spell_code,
        patient.family_name,
        patient.given_name,
        patient.middle_names,
        coalesce(patient.family_name, '') || ', ' || coalesce(patient.given_name, '') || ' ' || coalesce(patient.middle_names,'') as full_name,
        location.code as location,
        location.id as location_id,
        location.parent_id as ward_id,
        patient.sex,
        patient.dob,
        patient.other_identifier as hospital_number,
        patient.patient_identifier as nhs_number,
        extract(year from age(now(), patient.dob)) as age,
        ews0.next_diff_polarity ||
        case when extract(days from ews0.next_diff_interval) > 0
            then  extract(days from ews0.next_diff_interval) || ' day(s) ' else ''
        end || to_char(ews0.next_diff_interval, 'HH24:MI') next_diff,
        case ews0.frequency < 60
            when true then ews0.frequency || ' min(s)'
            else ews0.frequency/60 || ' hour(s) ' || ews0.frequency - ews0.frequency/60*60 || ' min(s)'
        end as frequency,
        case when ews1.id is null then 'none' else ews1.score::text end as ews_score_string,    
        ews1.score as ews_score,
        case
            when ews1.id is not null and ews2.id is not null and (ews1.score - ews2.score) = 0 then 'same'
            when ews1.id is not null and ews2.id is not null and (ews1.score - ews2.score) > 0 then 'down'
            when ews1.id is not null and ews2.id is not null and (ews1.score - ews2.score) < 0 then 'up'
            when ews1.id is null and ews2.id is null then 'none'
            when ews1.id is not null and ews2.id is null then 'first'
            when ews1.id is null and ews2.id is not null then 'no latest' -- shouldn't happen. 
        end as ews_trend_string,
        case when ews1.id is null then 'NoScore' else ews1.clinical_risk end as clinical_risk,
        ews1.score - ews2.score as ews_trend,
        param.height,
        param.o2target_level_id as o2target,
        case when param.mrsa then 'yes' else 'no' end as mrsa,
        case when param.diabetes then 'yes' else 'no' end as diabetes,
        case when param.pbp_monitoring then 'yes' else 'no' end as pbp_monitoring,
        case when param.weight_monitoring then 'yes' else 'no' end as weight_monitoring,
        cosulting_doctors.names as consultant_names
        
    from nh_clinical_spell spell
    inner join nh_activity spell_activity on spell_activity.id = spell.activity_id
    inner join nh_clinical_patient patient on spell.patient_id = patient.id
    left join nh_clinical_location location on location.id = spell.location_id
    left join ews ews1 on spell.id = ews1.spell_id and ews1.rank = 1 and ews1.state = 'completed'
    left join ews ews2 on spell.id = ews2.spell_id and ews2.rank = 2 and ews2.state = 'completed'
    left join ews ews0 on spell.id = ews0.spell_id and ews0.rank = 1 and ews0.state = 'scheduled'    
    left join cosulting_doctors on cosulting_doctors.spell_id = spell.id
    inner join param on param.spell_id = spell.id

    where spell_activity.state = 'started'
);

select * from nh_clinical_wardboard;




        """)