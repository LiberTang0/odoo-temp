import openerp, json
from openerp import http
from openerp.http import Root, Response
from openerp.modules.module import get_module_path
from datetime import datetime
from openerp.http import request
from werkzeug import utils, exceptions
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

class MobileFrontend(http.Controller):

    #def __init__(self, users, realm='login required'):
    #    self.users = users
    #    self.realm = realm

    @http.route('/api/patient/<patient_id>', type='http', auth='none')
    def get_patient(self, patient_id, *args, **kw):
        uid = self.authenticate(request)
        if uid:
            raw_patient_info = request.session.model('nh.clinical.patient').read([int(patient_id)])
            #patient_info = request.session.model('nh.eobs.api').get_patients([int(patient_id)])
            if len(raw_patient_info) > 0:
                patient_fhir = self.fhir_skeleton()
                patient_fhir['resourceType'] = 'Patient'
                patient = raw_patient_info[0]
                patient_fhir['name'] = self.process_patient_name(patient)
                patient_fhir['identifier'] = self.process_patient_identifier(patient)
                patient_fhir['telecom'] = self.process_patient_telecom(patient)
                patient_fhir['gender'] = self.process_patient_gender(patient)
                patient_fhir['birthDate'] = self.process_patient_birthdate(patient)
                patient_fhir['address'] = self.process_patient_address(patient)
                return request.make_response(json.dumps(patient_fhir), headers={'Content-Type': 'application/json'})
            else:
                return request.make_response(json.dumps({'status': 2, 'error': 'Patient not found'}), headers={'Content-Type': 'application/json'})
        else:
            return Response('Could not verify your access level for that URL.\n'
                            'You have to login with proper credentials', 401,
                            {'WWW-Authenticate': 'Basic realm="login required"'})

    def fhir_skeleton(self):
        fhir = {}
        fhir['resourceType'] = ''
        fhir['text'] = {}
        fhir['identifier'] = []
        fhir['name'] = []
        fhir['telecom'] = []
        fhir['gender'] = {}
        fhir['birthDate'] = ''
        fhir['deceasedBoolean'] = False
        fhir['address'] = []
        #fhir['contact'] = []
        #fhir['managingOrganization'] = {}
        fhir['active'] = True
        return fhir

    def process_patient_name(self, patient):
        names = []
        if 'family_name' in patient and 'given_name' in patient:
            oname = {}
            uname = {}
            oname['use'] = 'official'
            uname['use'] = 'usual'
            uname['given'] = patient['given_name'].split(',')
            oname['family'] = patient['family_name'].split('-')
            oname['given'] = patient['given_name'].split(',')
            if patient['middle_names']:
                middle_names = patient['middle_names'].split(',')
                for mname in middle_names:
                    oname['given'].append(mname)
            names.append(oname)
            names.append(uname)
        return names

    def process_patient_telecom(self, patient):
        telecom = []
        if patient['fax']:
            fax = {}
            fax['system'] = 'fax'
            fax['value'] = patient['fax']
            telecom.append(fax)
        if patient['mobile']:
            mobile = {}
            mobile['system'] = 'phone'
            mobile['value'] = patient['mobile']
            telecom.append(mobile)
        if patient['phone']:
            phone = {}
            phone['system'] = 'phone'
            phone['value'] = patient['phone']
            telecom.append(phone)
        if patient['email']:
            email = {}
            email['system'] = 'email'
            email['value'] = patient['email']
            telecom.append(email)
        return telecom

    def process_patient_gender(self, patient):
        gender = {}
        coding = []
        admin_gender = {}
        admin_gender['system'] = 'http://hl7.org/fhir/v3/AdministrativeGender'
        admin_gender['code'] = patient['gender']
        admin_gender['display'] = self.process_gender(patient['gender'])
        coding.append(admin_gender)
        gender['coding'] = coding
        return gender

    def process_patient_birthdate(self, patient):
        dob = patient['dob']
        date_of_birth = datetime.strptime(dob, DTF)
        return datetime.strftime(date_of_birth, '%Y-%m-%d')

    def process_patient_address(self, patient):
        addresses = []
        if patient['street'] or patient['street2'] or patient['city'] or patient['state_id'] or patient['zip']:
            home_address = {}
            home_address['use'] = 'home'
            if patient['street'] or patient['street2']:
                line = []
                if patient['street']:
                    line.append(patient['street'])
                if patient['street2']:
                    line.append(patient['street2'])
                home_address['line'] = line
            if patient['city']:
                home_address['city'] = patient['city']
            if patient['state_id']:
                home_address['state'] = request.session.model('res.country.state').read(patient['state_id'])['display_name']
            if patient['zip']:
                home_address['zip'] = patient['zip']
            addresses.append(home_address)
        return addresses

    def process_patient_identifier(self, patient):
        identifiers = []
        if patient['patient_identifier']:
            id = {}
            id['system'] = 'http://nhs.uk/fhir/nhs-number/'
            id['value'] = patient['patient_identifier']
            id['use'] = 'national'
            id['label'] = 'NHS Number'
            identifiers.append(id)

        #if patient['other_identifier']:

        return identifiers

    def process_text(self, patient):
        return {'status': 'generated'}


    def process_gender(self, gender):
        if gender.upper() == 'M':
            return 'Male'
        if gender.upper() == 'F':
            return 'Female'

    def authenticate(self, request):
        if request.httprequest.authorization and request.params.get('db'):
            return self.check_auth(request.params.get('db'), request.httprequest.authorization.username, request.httprequest.authorization.password)
        else:
            return False

    def check_auth(self, db, username, password):
        return request.session.authenticate(db, username, password)