from openerp.tests import common
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rd
from openerp import tools
from openerp.tools import config
from openerp.osv import orm, fields, osv
from pprint import pprint as pp
from openerp import SUPERUSER_ID
import logging
from pprint import pprint as pp
from openerp.addons.t4activity.activity import except_if
_logger = logging.getLogger(__name__)

from faker import Faker
fake = Faker()


class t4_clinical_api_demo(orm.AbstractModel):
    _name = 't4.clinical.api.demo'
    
    def __init__(self, pool, cr):
        self._fake = fake
        self._seed = self._fake.random_int(min=1000001, max=9999999)
        super(t4_clinical_api_demo, self).__init__(pool, cr)
         
    def next_seed_fake(self, seed=None):
        if seed:
            self._fake.seed(seed)
        else:
            self._seed += 1
            self._fake.seed(self._seed)
        return self._fake    
    
    def demo_data(self, cr, uid, model, values_method=None, values={}):
        api_demo_data = self.pool['t4.clinical.api.demo.data']
        values_method = values_method or api_demo_data._default_values_methods.get(model)
        except_if(not values_method, msg="Values method is not passed and default method is not set!")
        v = eval("api_demo_data.{method}(cr, uid, values)".format(method=values_method))
        return v        
    
    def create(self, cr, uid, model, values_method=None, values={}, context=None):
        model_pool = self.pool[model]
        v = self.demo_data(cr, uid, model, values_method, values)
        _logger.info("Creating DEMO resource '%s', values: %s" % (model, v))
        res_id = model_pool.create(cr, uid, v, context)
        return res_id
    
#     def get_activity_free_patient(self, cr, uid, pos_id, data_models, states, return_id=False):
#         # random_observation_available_location
#         fake.seed(next_seed())
#         api = self.pool['t4.clinical.api']
#              
#         all_patient_ids = [a.patient_id.id for a in api.get_activities(cr, SUPERUSER_ID, 
#                                 pos_ids=[pos_id], data_models=['t4.clinical.spell'], states=['started'])]
#         used_patient_ids = [a.patient_id.id for a in api.get_activities(cr, SUPERUSER_ID, data_models=data_models, states=states)]
#         patient_ids = list(set(all_patient_ids)-set(used_patient_ids))       
#         
#         return api.browse(cr, SUPERUSER_ID, 't4.clinical.patient', patient_ids)
    
    def create_activity(self, cr, uid, model, values_method=None, activity_values={}, data_values={}, context=None):
        model_pool = self.pool[model]
        print "create activity data_values: %s" % data_values
        v = self.demo_data(cr, uid, model, values_method, data_values)
        _logger.info("Creating DEMO resource '%s', values: %s" % (model, v))
        activity_id = model_pool.create_activity(cr, uid, activity_values, v, context)
        return activity_id
    
    def place_patient(self, cr, uid, pos_id, bed_location_id=None):
        patient_id = None
        raise orm.except_orm('Not Implemented', 'Method place patient is not implemented yet!')
        return patient_id
    
    def get_available_bed(self, cr, uid, location_ids=[], pos_id=None):
        """
        Method    
        """
        api = self.pool['t4.clinical.api']
        fake = self.next_seed_fake()
        # find available in passed location_ids
        if location_ids:
            location_ids = api.location_map(cr, uid, location_ids=location_ids, usages=['bed'], available_range=[1,1]).keys()
            if location_ids:
                return fake.random_element(location_ids)
        # ensure pos_id is set
        if not pos_id:
            pos_ids = self.pool['t4.clinical.pos'].search(cr, uid, [])
            if pos_ids:
                pos_id = pos_ids[0]
            else:
                raise orm.except_orm('POS not found!', 'pos_id was not passed and existing POS is not found.') 
        # try to find existing locations
        location_ids = api.location_map(cr, uid, location_ids=location_ids, pos_ids=[pos_id], usages=['bed'], available_range=[1,1]).keys()
        if location_ids:
            return fake.random_element(location_ids)
        # create new location
        ward_location_ids = api.location_map(cr, uid, pos_ids=[pos_id], usages=['ward']).keys()
        if not ward_location_ids:
            pos_location_ids = api.location_map(cr, uid, pos_ids=[pos_id], usages=['pos']).keys()[0]
            ward_location_id = self.create(cr, uid, 't4.clinical.location', 'location_ward', {'parent_id': pos_location_ids[0]})
        else:
            ward_location_id = fake.random_element(ward_location_ids)
        location_id = self.create(cr, uid, 't4.clinical.location', 'location_bed', {'parent_id': ward_location_id})
        return location_id
    
    def get_nurse(self, cr, uid):    
        api = self.pool['t4.clinical.api']
        nurse_uid = api.user_map(cr, uid, group_xmlids=['group_t4clinical_nurse']).keys()
        if uid in nurse_uid:
            nurse_uid = uid
        else:
            nurse_uid = nurse_uid and nurse_uid[0] or self.create(cr, uid, 'res.users', 'user_nurse')    
        return nurse_uid
    
    def user_add_location(self, cr, uid, user_id, location_id):
        """
        Adds location_id to user's responsibility location list
        """
        self.pool['res.users'].write(cr, uid, user_id, {'location_ids': ([4, location_id])})
        return 
        
    def get_adt_user(self, cr, uid, pos_id):
        """
        Returns ADT user id for pos_id
        If uid appears to be ADT user id, returns uid
        """
        api = self.pool['t4.clinical.api']
        adt_uid = api.user_map(cr, uid, group_xmlids=['group_t4clinical_adt'], pos_ids=[pos_id]).keys()
        if uid in adt_uid:
            adt_uid = uid
        else:
            adt_uid = adt_uid and adt_uid[0] or self.create(cr, uid, 'res.users', 'user_adt', {'pos_id': pos_id})    
        return adt_uid
    
    def register_admit(self, cr, uid, pos_id, register_values={}, admit_values={}):
        """
        Registers and admits patient to POS. Missing data will be generated
        """
        api = self.pool['t4.clinical.api']
        # ensure pos_id is set
        if not pos_id:
            pos_ids = self.pool['t4.clinical.pos'].search(cr, uid, [])
            if pos_ids:
                pos_id = pos_ids[0]
            else:
                raise orm.except_orm('POS not found!', 'pos_id was not passed and existing POS is not found.')         
        adt_uid = self.get_adt_user(cr, uid, pos_id)
        reg_activity_id = self.create_activity(cr, adt_uid, 't4.clinical.adt.patient.register', None, {}, register_values)
        reg_data = api.get_activity_data(cr, uid, reg_activity_id)
        admit_activity_id = self.create_activity(cr, adt_uid, 't4.clinical.adt.patient.admit', None, {}, reg_data)
        api.complete(cr, uid, admit_activity_id)   
        return admit_activity_id
             

        
    def register_admit_place(self, cr, uid, bed_location_id=None, register_values={}, admit_values={}):
        """
        Registers, admits and places patient into bed_location_id if vacant 
        otherwise found among existing ones or created.
        Missing data will be generated
        """        
        api = self.pool['t4.clinical.api']
        
        bed_location_id = self.get_available_bed(cr, uid, location_ids=[bed_location_id])
        bed_location = api.browse(cr, uid, 't4.clinical.location', bed_location_id)     
        pos_id = bed_location.pos_id.id      
        
        admit_activity_id = self.register_admit(cr, uid, pos_id, register_values, admit_values)
          
        admission_activity_id = api.activity_map(cr, uid, 
                                                  data_models=['t4.clinical.patient.admission'],
                                                  creator_ids=[admit_activity_id]).keys()[0]
                        
        placement_activity_id = api.activity_map(cr, uid, 
                                                  data_models=['t4.clinical.patient.placement'],
                                                  creator_ids=[admission_activity_id]).keys()[0]   
        
        api.submit_complete(cr, uid, placement_activity_id, {'location_id': bed_location_id})     
        return placement_activity_id     
    
    def build_patient(self, cr, uid, bed_location_id=None, nurse_user_id=None, wm_user_id=None,
                      ews_count=3, gcs_count=2):
        """
        Patients-centric method. Places patient and builds patient-related environment. 
        """    
        api = self.pool['t4.clinical.api']
        placement_activity_id = self.register_admit_place(cr, uid)
        placement_activity = api.browse(cr, uid, 't4.activity', placement_activity_id)
        patient_id = placement_activity.patient_id.id
        pos_id = placement_activity.pos_id.id
        if not nurse_user_id:
            nurse_user_id = self.get_nurse(cr, uid)
        print nurse_user_id
        import pdb; pdb.set_trace()
        self.user_add_location(cr, uid, nurse_user_id, placement_activity.location_id.id)
        if wm_user_id:
            self.user_add_location(cr, uid, wm_user_id, placement_activity.location_id.id)
        while ews_count + gcs_count > 0:
            if ews_count:
                ews_count -= 1
                ews = api.activity_map(cr, uid, 
                                      data_models=['t4.clinical.patient.observation.ews'],
                                      pos_ids=[pos_id],
                                      patient_ids=[patient_id],
                                      states=['new', 'scheduled']).values()[0]
                api.submit_complete(cr, nurse_user_id, ews['id'], self.demo_data(cr, uid, 't4.clinical.patient.observation.ews'))
      
            if gcs_count:
                gcs_count -= 1
        
        return True
        
    
    def build_bed(self, cr, uid, bed_location_id=None, pos_id=None, parent_location_id=None, nurse_user_id=None,
                   ews=3, gcs=3, blood_sugar=2):
        """
        Bed-centric method. Builds environment related to bed location. 
        """
    
    
    
    def build_ward(self, cr, uid, ward_location_id=None, pos_id=None, parent_location_id=None, nurse_user_id=None, wm_user_id=None,
                   ews=3, gcs=3, blood_sugar=2):
        """
        Ward-centric method. Builds environment related to bed location.
        """
    
    
    
    def build_uat_pos(self, cr, uid, 
                       bed_count=5, ward_count=2, 
                       patient_admit_count=10, patient_placement_count=5, 
                       ews_count=3, weight_count=3, blood_sugar_count=3,
                       height_count=3, o2target_count=3, mrsa_count=3, diabetes_count=3):
#                        adt_user_count=1, hca_count=2, nurse_count=2, doctor_count=2, ward_manager_count=2):
        """
        Creates UAT POS with set names, wards, beds
        Returns pos_id
        """
        # set user names. password == name
        hca_names = ['harold', 'helen']
        nurse_names = ['neil', 'norah']
        ward_manager_names = ['walter', 'wanda']
        doctor_names = ['dean', 'dana']
        
        assert patient_admit_count >= patient_placement_count, "%s >= %s" % (patient_admit_count, patient_placement_count)
        assert bed_count >= patient_placement_count, "%s >= %s" % (bed_count, patient_placement_count)
        
        fake = self.next_seed_fake()
        api = self.pool['t4.clinical.api']
        pos_id = self.create(cr, uid, 't4.clinical.pos')  
        
        adt_uid = self.create(cr, uid, 'res.users', 'user_adt', {'pos_id': pos_id})

        ward_ids = [self.create(cr, uid, 't4.clinical.location', 'location_ward') for i in range(ward_count)]
        bed_ids = [self.create(cr, uid, 't4.clinical.location', 'location_bed', {'parent_id': fake.random_element(ward_ids)}) 
                   for i in range(bed_count)]
        
        hca_ids = [self.create(cr, uid, 'res.users', 'user_hca', 
                     {'name': name, 'location_ids': [6, 0, bed_ids]}) 
                   for name in hca_names]
        nurse_ids = [self.create(cr, uid, 'res.users', 'user_nurse', 
                        {'name': name, 'location_ids': [6, 0, ward_ids]}) 
                     for name in nurse_names]
        ward_manager_ids = [self.create(cr, uid, 'res.users', 'user_ward_manager', 
                            {'name': name, 'location_ids': [6, 0, bed_ids+ward_ids]}) 
                            for name in ward_manager_names]
        doctor_ids = [self.create(cr, uid, 'res.users', 'user_doctor', 
                        {'name': name}) 
                      for name in doctor_names]
        
        admit_activity_ids = [self.create_activity(cr, adt_uid, 't4.clinical.adt.patient.admit') for i in range(patient_admit_count)]
        [api.complete(cr, uid, id) for id in admit_activity_ids]
        temp_bed_ids = [i for i in bed_ids]
        temp_placement_activity_ids = api.activity_map(cr, uid, 
                                                  data_models=['t4.clinical.patient.placement'],
                                                  pos_ids=[pos_id],
                                                  states=['new', 'scheduled']).keys()
                                                  

        
        #import pdb; pdb.set_trace()
        for i in range(patient_placement_count):
            placement_activity_id = fake.random_element(temp_placement_activity_ids)
            bed_location_id = fake.random_element(temp_bed_ids)
            api.submit_complete(cr, uid, placement_activity_id, {'location_id': bed_location_id})
            temp_placement_activity_ids.remove(placement_activity_id)
            temp_bed_ids.remove(bed_location_id)
            
        ews_activities = api.activity_map(cr, uid, 
                                          data_models=['t4.clinical.patient.observation.ews'],
                                          pos_ids=[pos_id],
                                          states=['new', 'scheduled']).values()
        #import pdb; pdb.set_trace()
        
        nurse_uid = fake.random_element(nurse_ids)
        #EWS
        for i in range(ews_count):
            for ews in ews_activities:
                api.assign(cr, uid, ews['id'], nurse_uid)
                api.submit_complete(cr, nurse_uid, ews['id'], self.demo_data(cr, uid, 't4.clinical.patient.observation.ews'))
            ews_activities = api.activity_map(cr, uid, 
                                          data_models=['t4.clinical.patient.observation.ews'],
                                          pos_ids=[pos_id],
                                          states=['new', 'scheduled']).values()              
        
        spell_activities = api.activity_map(cr, uid, 
                                          data_models=['t4.clinical.spell'],
                                          pos_ids=[pos_id],
                                          states=['started']).values()
        # WEIGHT
        for i in range(weight_count):
            for spell in spell_activities:
                vals = self.demo_data(cr, uid, 't4.clinical.patient.observation.weight', values={'patient_id': spell['patient_id']})
                api.create_complete(cr, uid,'t4.clinical.patient.observation.weight', {'parent_id': spell['id']}, vals)

        # BLOOD SUGAR
        for i in range(blood_sugar_count):
            for spell in spell_activities:
                vals = self.demo_data(cr, uid, 't4.clinical.patient.observation.blood_sugar', values={'patient_id': spell['patient_id']})
                api.create_complete(cr, uid, 't4.clinical.patient.observation.blood_sugar', {'parent_id': spell['id']}, vals)            

        # HEIGHT
        for i in range(height_count):
            for spell in spell_activities:
                vals = self.demo_data(cr, uid, 't4.clinical.patient.observation.height', values={'patient_id': spell['patient_id']})
                api.create_complete(cr, uid,'t4.clinical.patient.observation.height', {'parent_id': spell['id']}, vals)

        # DIABETES
        for i in range(diabetes_count):
            for spell in spell_activities:
                vals = self.demo_data(cr, uid, 't4.clinical.patient.diabetes', values={'patient_id': spell['patient_id']})
                api.create_complete(cr, uid,'t4.clinical.patient.diabetes', {'parent_id': spell['id']}, vals)

#         # O2TARGET
#         for i in range(o2target_count):
#             for spell in spell_activities:
#                 vals = self.demo_data(cr, uid, 't4.clinical.patient.o2target', values={'patient_id': spell['patient_id']})
#                 api.create_complete(cr, uid,'t4.clinical.patient.o2target', {'parent_id': spell['id']}, vals)        
        
        return True
#     def create_placement(self, cr, uid, values={}):
#         """
#         Must use adt user
#         """
#         fake = self.next_seed_fake()
#         api =self.pool['t4.clinical.api']
#         admit_activity_id = self.create_activity(cr, uid, 't4.clinical.adt.patient.admit')    
    
    

class t4_clinical_api_demo_data(orm.AbstractModel):
    _name = 't4.clinical.api.demo.data'

    _default_values_methods = {
        'res.users': 'user_nurse',
        't4.clinical.location': 'location_bed',
        't4.clinical.patient': 'patient',
        't4.clinical.pos': 'pos',
        't4.clinical.device': 'device',
        't4.clinical.device.type': 'device_type',
        
        't4.clinical.adt.patient.register': 'adt_register',
        't4.clinical.adt.patient.admit': 'adt_admit',
        't4.clinical.adt.patient.discharge': 'adt_discharge',
        
        't4.clinical.patient.observation.ews': 'observation_ews',
        't4.clinical.patient.observation.weight': 'observation_weight',
        't4.clinical.patient.observation.height': 'observation_height',
        't4.clinical.patient.observation.blood_sugar': 'observation_blood_sugar',
        
        't4.clinical.patient.diabetes': 'diabetes',
        
    }

    def __init__(self, pool, cr):
        self._fake = fake
        self._seed = self._fake.random_int(min=1000001, max=9999999)
        super(t4_clinical_api_demo_data, self).__init__(pool, cr)
        
    def next_seed_fake(self, seed=None):
        if seed:
            self._fake.seed(seed)
        else:
            self._seed += 1
            self._fake.seed(self._seed)
        return self._fake 

############# base ##############     

    ##### res.users #####
    def _user_base(self, cr, uid, values={}):        
        pos_id = values.get('pos_id', False)
        fake = self.next_seed_fake()
        api = self.pool['t4.clinical.api']
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "t4clinical_base", "group_t4clinical_nurse")
        location_ids = api.location_map(cr, uid, usages=['ward'], pos_ids=[pos_id])
        # unique login
        i = 0
        login = (values.get('name') or fake.first_name()).lower()
        while i <= 1000:
            if self.pool['res.users'].search(cr, uid, [('login','=',login)]):
                login = fake.first_name().lower()
                i += 1
            else:
                break
        if i > 1000:
            raise orm.except_orm("Demo data exception!","Failed to generate unique user login after 1000 attempts!")   
        v = {
            'name': login.capitalize(),
            'login': login,
            'password': login,
            'groups_id': [(4, group.id)],
            'location_ids': [(4,location_id) for location_id in location_ids]
        }  
        return v 
    
    def user_hca(self, cr, uid, values={}):
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "t4clinical_base", "group_t4clinical_hca")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})  
        v.update(values)
        return v        

    def user_nurse(self, cr, uid, values={}):
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "t4clinical_base", "group_t4clinical_nurse")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})  
        v.update(values)
        return v   

    def user_ward_manager(self, cr, uid, values={}):
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "t4clinical_base", "group_t4clinical_ward_manager")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})  
        v.update(values)
        return v 

    def user_doctor(self, cr, uid, values={}):
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "t4clinical_base", "group_t4clinical_doctor")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})  
        v.update(values)
        return v 

    def user_adt(self, cr, uid, values={}):
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "t4clinical_base", "group_t4clinical_adt")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})  
        if 'pos_id' not in values:
            api_demo = self.pool['t4.clinical.api.demo']
            v.update({'pos_id': api_demo.create(cr, uid, 't4.clinical.pos')})

        v.update(values)
        return v 
    
    
    #### location ####
    
    def location_pos(self, cr, uid, values={}):
        fake = self.next_seed_fake()        
        code = "POS_"+str(fake.random_int(min=100, max=999))
        v = {
               'name': "POS Location (%s)" % code,
               'code': code,
               'type': 'structural',
               'usage': 'hospital',
               }   
        v.update(values)     
        return v

    def location_discharge(self, cr, uid, values={}):
        fake = self.next_seed_fake()        
        code = "DISCHARGE_"+str(fake.random_int(min=100, max=999))
        v = {
               'name': "Discharge Location (%s)" % code,
               'code': code,
               'type': 'structural',
               'usage': 'room',
               }   
        v.update(values)     
        return v

    def location_admission(self, cr, uid, values={}):
        fake = self.next_seed_fake()        
        code = "ADMISSION_"+str(fake.random_int(min=100, max=999))
        v = {
               'name': "Admission Location (%s)" % code,
               'code': code,
               'type': 'structural',
               'usage': 'room',
               }   
        v.update(values)     
        return v

    def location_ward(self, cr, uid, values={}):
        fake = self.next_seed_fake()        
        code = "ward_"+str(fake.random_int(min=100, max=999))
        v = {
               'name': code,
               'code': code,
               'type': 'structural',
               'usage': 'ward',
               }   
        v.update(values)     
        return v

    def location_bed(self, cr, uid, values={}):
        fake = self.next_seed_fake()        
        code = "bed_"+str(fake.random_int(min=100, max=999))
        v = {
               'name': code,
               'code': code,
               'type': 'poc',
               'usage': 'bed',
               }   
        v.update(values)     
        return v

    #### patient ####
    def patient(self, cr, uid, values={}):
        fake = self.next_seed_fake()        
        name = fake.first_name()
        last_name =  fake.last_name(),
        gender = fake.random_element(('M','F'))
        v = {
                'name': name,
                'given_name': name,
                'family_name': last_name,
                'patient_identifier': "PI_"+str(fake.random_int(min=200000, max=299999)),
                'other_identifier': "OI_"+str(fake.random_int(min=100000, max=199999)),
                'dob': fake.date_time_between(start_date="-80y", end_date="-10y").strftime("%Y-%m-%d %H:%M:%S"),
                'gender': gender,
                'sex': gender,               
        }   
        v.update(values)     
        return v
    
    #### pos ####
    def pos(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        api_demo = self.pool['t4.clinical.api.demo']
        v = {'name': "(POS) HOSPITAL_"+str(fake.random_int(min=100, max=999))}
        if 'location_id' not in values:
            v.update({'location_id': api_demo.create(cr, uid, 't4.clinical.location', 'location_pos')})
        if 'lot_admission_id' not in values:
            v.update({'lot_admission_id': api_demo.create(cr, uid, 't4.clinical.location', 'location_admission')})
        if 'lot_discharge_id' not in values:
            v.update({'lot_discharge_id': api_demo.create(cr, uid, 't4.clinical.location', 'location_discharge')})
   
        v.update(values)     
        return v    
    
    #### device.type ####
    def device_type(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        flow_directions = dict(self.pool['t4.clinical.device.type']._columns['flow_direction'].selection).keys()
        v = {
            'name': "DEVICE_TYPE_"+str(fake.random_int(min=100, max=999)),
            'flow_direction': fake.random_element(flow_directions),
        }
        return v  
    
    #### device ####
    def device(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        if not 'type_id' in values:
            type_id = fake.random_element(self.pool['t4.clinical.device.type'].search(cr, uid, []))
            if not type_id:
                api_demo = self.pool['t4.clinical.api.demo']
                type_id = api_demo.create(cr, uid, 't4.clinical.device.type') 
        else:
            type_id = values['type_id']
        v = {
            'type_id': type_id
        }
        v.update(values)
        return v
    
######### activity types ###########        
    def adt_register(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        gender = fake.random_element(('M','F'))
        v = {
                'family_name': fake.last_name(),
                'given_name': fake.first_name(),
                'other_identifier': str(fake.random_int(min=1000001, max=9999999)),
                'dob': fake.date_time_between(start_date="-80y", end_date="-10y").strftime("%Y-%m-%d %H:%M:%S"),
                'gender': gender,
                'sex': gender,
                }
        v.update(values)
        return v
    
    def adt_admit(self, cr, uid, values={}):
        print values
        fake = self.next_seed_fake()
        api =self.pool['t4.clinical.api']
        api_demo = self.pool['t4.clinical.api.demo']
        #import pdb; pdb.set_trace()
        v = {}
        # if 'other_identifier' not passed register new patient and use it's data
        pos_id = 'pos_id' in values and values.pop('pos_id') or False
        if 'other_identifier' not in values:
            reg_activity_id = api_demo.create_activity(cr, uid, 't4.clinical.adt.patient.register')
            reg_data = api.get_activity_data(cr, uid, reg_activity_id)
            v.update({'other_identifier': reg_data['other_identifier']})
            pos_id = reg_data['pos_id']
        if 'location' not in values:
            ward_ids = api.location_map(cr, uid, pos_ids=[pos_id], usages=['wards']).keys()
            if not ward_ids:
                pos = self.pool['t4.clinical.pos'].browse(cr, uid, api.user_map(cr, uid, user_ids=[uid])[uid]['pos_id'])
                ward_location_id = api_demo.create(cr, uid, 't4.clinical.location', 'location_ward', {'parent_id': pos.location_id.id})
                ward_ids = [ward_location_id]
                ward_id = fake.random_element(ward_ids)
                ward = api.location_map(cr, uid, location_ids=[ward_id]).values()[0]
            v.update({'location': ward['code']})
        v.update(values)
        return v      
    
    def adt_discharge(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        api =self.pool['t4.clinical.api']
        patient_ids = [a['patient_id'] for a in api.activity_map(cr, uid, data_models=['t4.clinical.spell'], states=['started']).values()]
        patient = fake.random_element(api.patient_map(cr, uid, patient_ids=patient_ids).values()) 
        v = {
            'other_identifier': patient.get('other_identifier', "No patients to discharge!"),
        }
        v.update(values)
        return v
    
    def observation_ews(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        pos_id = 'pos_id' in values and values.pop('pos_id') or False
        
        #patients = self.get_activity_free_patients(cr, uid, env_id,['t4.clinical.patient.observation.ews'],['new','scheduled','started'])
        v = {
            'respiration_rate': fake.random_int(min=5, max=34),
            'indirect_oxymetry_spo2': fake.random_int(min=85, max=100),
            'body_temperature': float(fake.random_int(min=350, max=391))/10.0 ,
            'blood_pressure_systolic': fake.random_int(min=65, max=206),
            'pulse_rate': fake.random_int(min=35, max=136),
            'avpu_text': fake.random_element(('A', 'V', 'P', 'U')),
            'oxygen_administration_flag': fake.random_element((True, False)),
            'blood_pressure_diastolic': fake.random_int(min=35, max=176),
            #'patient_id': patients and fake.random_element(patients).id or False
        }
        v.update(values) # in case the flag passed in values
        if v['oxygen_administration_flag']:
            v.update({
                'flow_rate': fake.random_int(min=40, max=60),
                'concentration': fake.random_int(min=50, max=100),
                'cpap_peep': fake.random_int(min=1, max=100),
                'niv_backup': fake.random_int(min=1, max=100),
                'niv_ipap': fake.random_int(min=1, max=100),
                'niv_epap': fake.random_int(min=1, max=100),
            })
#         if not d['patient_id']:
#             _logger.warn("No patients available for ews!")
        v.update(values)
        return v          
        
    def observation_weight(self, cr, uid, values={}):
        api = self.pool['t4.clinical.api']
        api_demo = self.pool['t4.clinical.api.demo']
        fake = self.next_seed_fake()
        v = {}
#         pos_id = 'pos_id' in values and values.pop('pos_id') or False
#         
#         assert 'patient_id' in values or pos_id, "patient_id and pos_id are not in values, can't provide patient_id!"
#         assert 'parent_id' in values or pos_id, "parent_id and pos_id are not in values, can't provide parent_id!"
#         if 'patient_id' not in values or 'parent_id' not in values:
#             spells = api.activity_map(cr, uid, pos_ids=[pos_id], data_models=['t4.clinical.spell'], states=['started'])
#             weights = api.activity_map(cr, uid, pos_ids=[pos_id], data_models=['t4.clinical.patient.observation.weight'], states=['new', 'started'])
#             weight_patient_ids = [w['pateint_id'] for w in weights]
#             spells = [s for s in spells if s['patient_id'] not in weight_patient_ids]
#             if not spells:
#                 api_demo.place_patient(cr, uid, pos_id)
#                 spells = api.activity_map(cr, uid, pos_ids=[pos_id], data_models=['t4.clinical.spell'], states=['started'])
#             update_vals = [{'patient_id': s['patient_id'], 'parent_id': s['id']}  for s in spells]
#             v.update(fake.random_element(update_vals))
        assert 'patient_id' in values, "'patient_id' is not in values!"
        v.update({'weight': float(fake.random_int(min=40, max=200))})
        v.update(values)
        return v        

    def observation_height(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        v = {}
        assert 'patient_id' in values, "'patient_id' is not in values!"
        v.update({'height': float(fake.random_int(min=120, max=220))})
        v.update(values)
        return v  

    def diabetes(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        v = {}
        assert 'patient_id' in values, "'patient_id' is not in values!"
        v.update({'diabetes': fake.random_element([True, False])})
        v.update(values)
        return v  
    
    def observation_blood_sugar(self, cr, uid, values={}):
        fake = self.next_seed_fake()
        v = {
             'blood_sugar': float(fake.random_int(min=1, max=100)),
             #'patient_id': fake.random_element(self.get_current_patient_ids(cr, SUPERUSER_ID, env_id))
        }
        v.update(values)
        return v
        