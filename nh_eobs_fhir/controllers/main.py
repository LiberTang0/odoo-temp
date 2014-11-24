import openerp, json
from openerp import http
from openerp.http import Root, Response
from openerp.modules.module import get_module_path
from datetime import datetime
from openerp.http import request
from werkzeug import utils, exceptions
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

class FHIRAPI(http.Controller):


    @http.route('/api/v1/Patient', type='http', auth='none')
    def search_patients(self, *args, **kw):
        uid = self.authenticate(request)
        if uid:
            # get the params from the URL and turn into a search domain
            search_domain = []
            for k,v in request.params.iteritems():
                if k in ['_id', '_language', 'active', 'address', 'animal-breed', 'animal-species', 'birthdate', 'family', 'gender', 'given', 'identifier', 'language', 'link', 'name', 'phonetic', 'provider', 'telecom']:
                    search_domain.append([self.process_search_key(k),'=',v])
            # Do a search with the domain
            patient_ids = request.session.model('nh.clinical.patient').search(search_domain)
            patients = []
            for patient_id in patient_ids:
                patient_to_add = {}
                patient_to_add['id'] = patient_id
                patient_to_add['category'] = []
                patient_to_add['content'] = self.process_patient_fhir(patient_id)
                patients.append(patient_to_add)
            search_response = {}
            search_response['resourceType'] = 'Bundle'
            search_response['title'] = 'Search result'
            search_response['link'] = [{'rel': 'self', 'href': request.httprequest.url}]
            search_response['entry'] = patients
            return request.make_response(json.dumps(search_response), headers={'Content-Type': 'application/json'})
        else:
            return Response('Could not verify your access level for that URL.\n'
                            'You have to login with proper credentials', 401,
                            {'WWW-Authenticate': 'Basic realm="login required"'})

    @http.route('/api/v1/Patient/<patient_id>', type='http', auth='none')
    def read_patients(self, patient_id, *args, **kw):
        uid = self.authenticate(request)
        if uid:
            patient = self.process_patient_fhir(int(patient_id))
            patient['resourceType'] = 'Patient'
            return request.make_response(json.dumps(patient), headers={'Content-Type': 'application/json'})
        else:
            return Response('Could not verify your access level for that URL.\n'
                            'You have to login with proper credentials', 401,
                            {'WWW-Authenticate': 'Basic realm="login required"'})

    def process_patient_fhir(self, id):
        raw_patient_info = request.session.model('nh.clinical.patient').read([id])
        #patient_info = request.session.model('nh.eobs.api').get_patients([int(patient_id)])
        if len(raw_patient_info) > 0:
            patient_fhir = self.fhir_skeleton()
            # patient_fhir['resourceType'] = 'Patient'
            patient = raw_patient_info[0]
            patient_fhir['name'] = self.process_patient_name(patient)
            patient_fhir['identifier'] = self.process_patient_identifier(patient)
            # patient_fhir['telecom'] = self.process_patient_telecom(patient)
            patient_fhir['gender'] = self.process_patient_gender(patient)
            patient_fhir['birthDate'] = self.process_patient_birthdate(patient)
            patient_fhir['address'] = self.process_patient_address(patient)
        return patient_fhir

    def fhir_skeleton(self):
        fhir = {}
        fhir['resourceType'] = ''
        # fhir['text'] = {}
        fhir['identifier'] = []
        fhir['name'] = []
        # fhir['telecom'] = []
        fhir['gender'] = {}
        fhir['birthDate'] = ''
        # fhir['deceasedBoolean'] = False
        fhir['address'] = []
        #fhir['contact'] = []
        #fhir['managingOrganization'] = {}
        # fhir['active'] = True
        return fhir

    def process_patient_name(self, patient):
        names = []
        if 'family_name' in patient and 'given_name' in patient:
            oname = {}
            uname = {}
            oname['use'] = 'official'
            uname['use'] = 'usual'
            oname['prefix'] = patient['title'][1] if patient['title'] else ''
            uname['given'] = patient['given_name'].split(',')
            oname['family'] = patient['family_name'].split('-')
            oname['given'] = patient['given_name'].split(',')
            oname['text'] = patient['full_name']
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
        return datetime.strftime(date_of_birth, '%Y-%m-%dT%H:%M:%S.000Z')

    def process_patient_address(self, patient):
        addresses = []
        if patient['street'] or patient['street2'] or patient['city'] or patient['state_id'] or patient['zip']:
            home_address = {}
            home_address['use'] = 'home'
            text_address = []
            if patient['street'] or patient['street2']:
                line = []
                if patient['street']:
                    line.append(patient['street'])
                if patient['street2']:
                    line.append(patient['street2'])
                home_address['line'] = line
                text_address.append(', '.join(line))
            if patient['city']:
                home_address['city'] = patient['city']
                text_address.append(patient['city'])
            if patient['state_id']:
                home_address['state'] = request.session.model('res.country.state').read(patient['state_id'])['display_name']
                text_address.append(patient['state'])
            if patient['zip']:
                home_address['zip'] = patient['zip']
                text_address.append(patient['zip'])

            home_address['text'] = ', '.join(text_address)
            addresses.append(home_address)
        return addresses

    def process_patient_identifier(self, patient):
        identifiers = []
        if patient['patient_identifier']:
            id = {}
            id['system'] = 'NHS'
            id['value'] = patient['patient_identifier']
            id['use'] = 'national'
            id['label'] = 'NHS Number'
            identifiers.append(id)

        if patient['other_identifier']:
            id = {}
            id['system'] = 'Hospital'
            id['value'] = patient['other_identifier']
            id['use'] = 'hospital'
            id['label'] = 'Hospital Number'
            identifiers.append(id)

        if patient['id']:
            id = {}
            id['system'] = 'Open-eObs'
            id['value'] = patient['id']
            id['use'] = 'Open-eObs'
            id['label'] = 'Open-eObs ID'
            identifiers.append(id)

        return identifiers

    def process_text(self, patient):
        return {'status': 'generated'}


    def process_gender(self, gender):
        if gender.upper() == 'M':
            return 'Male'
        if gender.upper() == 'F':
            return 'Female'

    def authenticate(self, request):
        # return self.check_auth(request.params.get('db'), 'fhir_api', 'fhir_api')
        if request.httprequest.authorization and request.params.get('db'):
            return self.check_auth(request.params.get('db'), request.httprequest.authorization.username, request.httprequest.authorization.password)
        else:
            return False

    def check_auth(self, db, username, password):
        return request.session.authenticate(db, username, password)

    def process_search_key(self, key):
        if key == 'identifier':
            return 'patient_identifier'
        elif key == 'given':
            return 'given_name'
        elif key == 'family':
            return 'family_name'
        elif key == 'name':
            return 'full_name'
        elif key == 'gender':
            return 'gender'
        elif key == '_id':
            return 'id'
        else:
            return 'id'