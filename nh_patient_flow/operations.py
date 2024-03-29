from openerp.osv import orm, fields
from openerp.addons.nh_activity.activity import except_if
from openerp import SUPERUSER_ID


class nh_clinical_patient_referral(orm.Model):
    """
    Represents external patient referrals that are entered into the system but the patients have not arrived yet to the specified location.
    * Usually handled by receptionist users.
    * Whenever it's completed means that the patient has arrived and it is moved to the specified location.
    """
    _name = 'nh.clinical.patient.referral'
    _inherit = ['nh.activity.data']
    _description = "Patient Referral"
    _start_view_xmlid = "view_patient_referral_form"
    _schedule_view_xmlid = "view_patient_referral_form"
    _submit_view_xmlid = "view_patient_referral_form"
    _complete_view_xmlid = "view_patient_referral_complete"
    _cancel_view_xmlid = "view_patient_referral_form"

    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Destination Location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'pos_id': fields.related('activity_id', 'pos_id', type='many2one', relation='nh.clinical.pos', string='POS'),
    }

    def get_activity_location_id(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        return activity.data_ref.location_id.id

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        move_pool = self.pool['nh.clinical.patient.move']
        referral_activity = activity_pool.browse(cr, uid, activity_id, context)
        except_if(not referral_activity.data_ref.location_id,
                  msg="Location is not set, referral can't be completed! activity.id = %s" % referral_activity.id)
        res = super(nh_clinical_patient_referral, self).complete(cr, uid, activity_id, context)

        referral_activity = activity_pool.browse(cr, uid, activity_id, context)
        # set spell location
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, SUPERUSER_ID, referral_activity.data_ref.patient_id.id, context=context)
        except_if(not spell_activity_id,
                  cap="Spell in state 'started' is not found for patient_id=%s" % referral_activity.data_ref.patient_id.id,
                  msg="Referral can not be completed")
        # move to location
        move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,
                                                    {'parent_id': spell_activity_id,
                                                     'creator_id': activity_id},
                                                    {'patient_id': referral_activity.data_ref.patient_id.id,
                                                     'location_id': referral_activity.data_ref.location_id.id})
        activity_pool.complete(cr, SUPERUSER_ID, move_activity_id)
        activity_pool.submit(cr, SUPERUSER_ID, spell_activity_id, {'location_id': referral_activity.data_ref.location_id.id})
        # trigger referral policy activities
        self.trigger_policy(cr, uid, activity_id, location_id=referral_activity.data_ref.location_id.id, context=context)
        return res