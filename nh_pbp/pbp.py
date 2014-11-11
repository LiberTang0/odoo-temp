# -*- coding: utf-8 -*-
from openerp.osv import orm, fields
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
import logging
from openerp import SUPERUSER_ID


_logger = logging.getLogger(__name__)


class nh_clinical_patient_observation_pbp(orm.Model):
    _name = 'nh.clinical.patient.observation.pbp'
    _inherit = ['nh.clinical.patient.observation']
    _required = ['systolic_sitting', 'diastolic_sitting', 'systolic_standing', 'diastolic_standing']
    _description = "Postural Blood Pressure Observation"

    _POLICY = {'schedule': [[6, 0], [18, 0]], 'notifications': [
        [],
        [{'model': 'nurse', 'summary': 'Inform FY2', 'groups': ['nurse', 'hca']},
         {'model': 'hca', 'summary': 'Inform registered nurse', 'groups': ['hca']},
         {'model': 'nurse', 'summary': 'Informed about patient status (Postural Blood Pressure)', 'groups': ['hca']}]
    ]}

    def _get_pbp_result(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for pbp in self.browse(cr, uid, ids, context=context):
            if int(pbp.systolic_sitting - pbp.systolic_standing) > 20:
                res[pbp.id] = 'yes'
            else:
                res[pbp.id] = 'no'
        return res

    _columns = {
        'systolic_sitting': fields.integer('Sitting Blood Pressure Systolic'),
        'systolic_standing': fields.integer('Standing Blood Pressure Systolic'),
        'diastolic_sitting': fields.integer('Sitting Blood Pressure Diastolic'),
        'diastolic_standing': fields.integer('Standing Blood Pressure Diastolic'),
        'result': fields.function(_get_pbp_result, type='char', string='>20 mm/Hg', size=5, store=False)
    }

    _form_description = [
        {
            'name': 'systolic_sitting',
            'type': 'integer',
            'label': 'Sitting Blood Pressure Systolic',
            'min': 1,
            'max': 300,
            'validation': [['>', 'diastolic_sitting']],
            'initially_hidden': False
        },
        {
            'name': 'diastolic_sitting',
            'type': 'integer',
            'label': 'Sitting Blood Pressure Diastolic',
            'min': 1,
            'max': 280,
            'validation': [['<', 'systolic_sitting']],
            'initially_hidden': False
        },
        {
            'name': 'systolic_standing',
            'type': 'integer',
            'label': 'Standing Blood Pressure Systolic',
            'min': 1,
            'max': 300,
            'validation': [['>', 'diastolic_standing']],
            'initially_hidden': True
        },
        {
            'name': 'diastolic_standing',
            'type': 'integer',
            'label': 'Standing Blood Pressure Diastolic',
            'min': 1,
            'max': 280,
            'validation': [['<', 'systolic_standing']],
            'initially_hidden': True
        }
    ]

    def schedule(self, cr, uid, activity_id, date_scheduled=None, context=None):
        hour = td(hours=1)
        schedule_times = []
        for s in self._POLICY['schedule']:
            schedule_times.append(dt.now().replace(hour=s[0], minute=s[1], second=0, microsecond=0))
        date_schedule = date_scheduled if date_scheduled else dt.now().replace(minute=0, second=0, microsecond=0)
        utctimes = [fields.datetime.utc_timestamp(cr, uid, t, context=context) for t in schedule_times]
        while all([date_schedule.hour != date_schedule.strptime(ut, DTF).hour for ut in utctimes]):
            date_schedule += hour
        return super(nh_clinical_patient_observation_pbp, self).schedule(cr, uid, activity_id, date_schedule.strftime(DTF), context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Implementation of the default PBP policy
        """
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        groups_pool = self.pool['res.groups']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        case = int(activity.data_ref.result == 'yes')
        hcagroup_ids = groups_pool.search(cr, uid, [('users', 'in', [uid]), ('name', '=', 'NH Clinical HCA Group')])
        nursegroup_ids = groups_pool.search(cr, uid, [('users', 'in', [uid]), ('name', '=', 'NH Clinical Nurse Group')])
        group = nursegroup_ids and 'nurse' or hcagroup_ids and 'hca' or False

        # TRIGGER NOTIFICATIONS
        api_pool.trigger_notifications(cr, uid, {
            'notifications': self._POLICY['notifications'][case],
            'parent_id': activity.parent_id.id,
            'creator_id': activity_id,
            'patient_id': activity.data_ref.patient_id.id,
            'model': self._name,
            'group': group
        }, context=context)

        res = super(nh_clinical_patient_observation_pbp, self).complete(cr, uid, activity_id, context)

        api_pool.cancel_open_activities(cr, uid, activity.parent_id.id, self._name, context=context)

        # create next PBP (schedule)
        domain = [
            ['data_model', '=', 'nh.clinical.patient.pbp_monitoring'],
            ['state', '=', 'completed'],
            ['patient_id', '=', activity.data_ref.patient_id.id]
        ]
        pbp_monitoring_ids = activity_pool.search(cr, uid, domain, order="date_terminated desc, sequence desc", context=context)
        monitoring_active = pbp_monitoring_ids and activity_pool.browse(cr, uid, pbp_monitoring_ids[0], context=context).data_ref.pbp_monitoring
        if monitoring_active:
            next_activity_id = self.create_activity(cr, SUPERUSER_ID,
                                 {'creator_id': activity_id, 'parent_id': activity.parent_id.id},
                                 {'patient_id': activity.data_ref.patient_id.id})

            date_schedule = dt.now().replace(minute=0, second=0, microsecond=0) + td(hours=2)

            activity_pool.schedule(cr, uid, next_activity_id, date_schedule, context=context)
        return res