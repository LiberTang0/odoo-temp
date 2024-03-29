# -*- coding: utf-8 -*-
from openerp.osv import orm, fields, osv
import logging        
from pprint import pprint as pp
from openerp import SUPERUSER_ID
_logger = logging.getLogger(__name__)


class nh_clinical_demo_discharge(orm.TransientModel):    
    _name = 'nh.clinical.demo.discharge'
    
    _columns = {
                
        'other_identifier': fields.text('otherId', required=True),
        'discharge_date': fields.datetime('Discharge Date')
   
        
    } 
    
    def default_get(self, cr, uid, fields, context=None):
        api_demo = self.pool['nh.clinical.api.demo']
        res = {}.fromkeys(fields)
        data = api_demo.demo_data(cr, uid, "nh.clinical.adt.patient.discharge")
        res.update(data)
        #pos_id = self.pool['nh.clinical.pos'].search(cr, uid, [])[0]
        #res.update({'pos_id': pos_id})
        return res 

    def submit(self, cr, uid, ids, context=None):
        api = self.pool['nh.clinical.api']
        api_demo = self.pool['nh.clinical.api.demo']
        data = self.read(cr, uid, ids[0], [])
        data.pop('id')
        
        patient_ids = api.search(cr, uid, 'nh.clinical.patient', [['other_identifier','=',data['other_identifier']]])
        pos_id = None
        spell_activity_id = None
        if patient_ids:
            spell_activity = api.activity_map(cr, uid, data_models=['nh.clinical.spell'], states=['started'], patient_ids=patient_ids)
            pos_id = spell_activity and spell_activity.values()[0]['pos_id']
            
        
        if not pos_id:
            raise orm.except_orm("Invalid OtherID", "Either patient or spell not found for Other ID '%s'" % data['other_identifier'])

        adt_uid = api.user_map(cr, uid, group_xmlids=['group_nhc_adt'], pos_ids=[pos_id]).keys()
        adt_uid = adt_uid and adt_uid[0] or api_demo.create(cr, uid, 'res.users', 'user_adt', {'pos_id': pos_id})
        
        discharge_activity_id = api.create_complete(cr, adt_uid, 'nh.clinical.adt.patient.discharge', {}, data)




class nh_clinical_demo_location(orm.TransientModel):    
    _name = 'nh.clinical.demo.location'
    
    _columns = {        
        'name': fields.char('Name', size=256),
        'code': fields.char('Code', size=256),
        'type': fields.selection(lambda s, cr, u, context=None: s.pool['nh.clinical.location']._columns['type'].selection, 'Type'),
        'usage': fields.selection(lambda s, cr, u, context=None: s.pool['nh.clinical.location']._columns['usage'].selection, 'Usage'),
        'parent_id': fields.many2one('nh.clinical.location', 'Parent Location')
    } 
    
    def default_get(self, cr, uid, fields, context=None):
        api_demo = self.pool['nh.clinical.api.demo']
        api = self.pool['nh.clinical.api']
        res = {}.fromkeys(fields)
        parent_id = api.location_map(cr, uid, usages=['ward']).keys()[0]
        data = api_demo.demo_data(cr, uid, 'nh.clinical.location', 'location_bed', {'parent_id': parent_id})
        res.update(data)
        return res 

    def submit(self, cr, uid, ids, context=None):
        api = self.pool['nh.clinical.api']
        data = self.read(cr, uid, ids[0], [])
        data.pop('id')
        parent_id = data.pop('parent_id')[0]
        data.update({'parent_id': parent_id}) 
        location_id = api.create(cr, uid, 'nh.clinical.location', data)

 
class nh_clinical_demo_user(orm.TransientModel):    
    _name = 'nh.clinical.demo.user'
    _columns = {        
        'name': fields.char('Name', size=256),
        'login': fields.char('Login', size=256),
        'password': fields.char('Password', size=256),
        'groups_id': fields.many2many('res.groups', relation='wiz_user_group_rel', string='Groups', domain=[['name','like','NH Clinical%%']]),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location_ids': fields.many2many('nh.clinical.location', relation='wiz_user_location_rel', string='POS'),
    } 
    
    def default_get(self, cr, uid, fields, context=None):
        api_demo = self.pool['nh.clinical.api.demo']
        res = {}.fromkeys(fields)
        pos_id = self.pool['nh.clinical.pos'].search(cr, uid, [])[0]
        data = api_demo.demo_data(cr, uid, 'res.users', 'user_adt', {'pos_id': pos_id})
        res.update(data)
        res.update({'pos_id': pos_id})
        res.update({'groups_id': [data['groups_id'][0][1]]})
        return res 

    def submit(self, cr, uid, ids, context=None):
        api = self.pool['nh.clinical.api']
        data = self.read(cr, uid, ids[0], [])
        data.pop('id')
        pos_id = data.pop('pos_id')[0]
        groups_id = [[4, id] for id in data.pop('groups_id') or []]
        location_ids = [[4, id] for id in data.pop('location_ids') or []]
        data.update({'groups_id': groups_id, 'pos_id': pos_id, 'location_ids': location_ids}) 
        user_id = api.create(cr, uid, 'res.users', data)
        


class nh_clinical_demo_register(orm.TransientModel):    
    _name = 'nh.clinical.demo.register'
    
    _columns = {
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),        
        'dob': fields.datetime('Date Of Birth'),
        'sex': fields.char('Sex', size=1),
        'gender': fields.char('Gender', size=1),
        'patient_identifier': fields.char('Patient Identifier', size=100),
        'other_identifier': fields.char('Other Identifier', size=100),
        'given_name': fields.char('Given Name', size=200),
        'middle_names': fields.char('Middle Name(s)', size=200),
        'family_name': fields.char('Family Name', size=200),
   
        
    } 
    
    def default_get(self, cr, uid, fields, context=None):
        api_demo = self.pool['nh.clinical.api.demo']
        res = {}.fromkeys(fields)
        data = api_demo.demo_data(cr, uid, "nh.clinical.adt.patient.register")
        res.update(data)
        pos_id = self.pool['nh.clinical.pos'].search(cr, uid, [])[0]
        res.update({'pos_id': pos_id})
        return res 

    def submit(self, cr, uid, ids, context=None):
        api = self.pool['nh.clinical.api']
        api_demo = self.pool['nh.clinical.api.demo']
        data = self.read(cr, uid, ids[0], [])
        data_copy = data.copy()
        data_copy.pop('id')
        pos_id = data_copy.pop('pos_id')[0]

        adt_uid = api.user_map(cr, uid, group_xmlids=['group_nhc_adt'], pos_ids=[pos_id]).keys()
        adt_uid = adt_uid and adt_uid[0] or api_demo.create(cr, uid, 'res.users', 'user_adt', {'pos_id': pos_id})
        
        reg_activity_id = api_demo.create_activity(cr, adt_uid, 'nh.clinical.adt.patient.register', None, {}, data_copy)
        reg_data = api.get_activity_data(cr, uid, reg_activity_id)


class nh_clinical_demo_placement(orm.TransientModel):    
    _name = 'nh.clinical.demo.placement'
    
    _columns = {
        'bed_location_id':  fields.many2one('nh.clinical.location', 'Bed Location', domain=[['usage','=','bed']], required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        
        'dob': fields.datetime('Date Of Birth'),
        'sex': fields.char('Sex', size=1),
        'gender': fields.char('Gender', size=1),
        'patient_identifier': fields.char('Patient Identifier', size=100),
        'other_identifier': fields.char('Other Identifier', size=100),
        'given_name': fields.char('Given Name', size=200),
        'middle_names': fields.char('Middle Name(s)', size=200),
        'family_name': fields.char('Family Name', size=200),
   
        
    } 
    
    def default_get(self, cr, uid, fields, context=None):
        api_demo = self.pool['nh.clinical.api.demo']
        api = self.pool['nh.clinical.api']
        res = {}.fromkeys(fields)
        data = api_demo.demo_data(cr, uid, "nh.clinical.adt.patient.register")
        res.update(data)
        pos_id = self.pool['nh.clinical.pos'].search(cr, uid, [])[0]
        bed_id = api.location_map(cr, uid, usages=['bed'], pos_ids=[pos_id]).keys()[0]
        res.update({'pos_id': pos_id, 'bed_location_id': bed_id})
        return res    
    
    def submit(self, cr, uid, ids, context=None):
        api = self.pool['nh.clinical.api']
        api_demo = self.pool['nh.clinical.api.demo']
        data = self.read(cr, uid, ids[0], [])
        data_copy = data.copy()
        data_copy.pop('id')
        bed_location_id = data_copy.pop('bed_location_id')[0]
        pos_id = data_copy.pop('pos_id')[0]

        adt_uid = api.user_map(cr, uid, group_xmlids=['group_nhc_adt'], pos_ids=[pos_id]).keys()
        adt_uid = adt_uid and adt_uid[0] or api_demo.create(cr, uid, 'res.users', 'user_adt', {'pos_id': pos_id})
        
        reg_activity_id = api_demo.create_activity(cr, adt_uid, 'nh.clinical.adt.patient.register', None, {}, data_copy)
        reg_data = api.get_activity_data(cr, uid, reg_activity_id)
        admit_activity_id = api_demo.create_activity(cr, adt_uid, 'nh.clinical.adt.patient.admit', None, {}, reg_data)
        api.complete(cr, uid, admit_activity_id)

        admission_activity_id = api.activity_map(cr, uid, 
                                                  data_models=['nh.clinical.patient.admission'],
                                                  creator_ids=[admit_activity_id]).keys()[0]
                        
        placement_activity_id = api.activity_map(cr, uid, 
                                                  data_models=['nh.clinical.patient.placement'],
                                                  creator_ids=[admission_activity_id]).keys()[0]   
        
        api.submit_complete(cr, uid, placement_activity_id, {'location_id': bed_location_id})
