#!/usr/bin/env python
#
# Citizen Desk
#

import datetime
import uuid
from bson.objectid import ObjectId

try:
    unicode
except:
    unicode = str

from citizendesk.common.utils import get_id_value as _get_id_value
from citizendesk.feeds.any.report.storage import collection, schema, FIELD_UPDATED, FIELD_UUID
from citizendesk.feeds.any.report.storage import get_report_by_id, update_report_set
from citizendesk.feeds.any.coverage.storage import get_coverage_by_id, get_coverage_by_uuid

COVERAGE_SETS = ('targeting', 'published', 'outgested')

'''
coverages: {
    'targeting': [id_a, id_z],
    'published': [id_a, id_b],
    'outgested': [id_a, id_b, id_c],
}
'''

def do_publish_one(db, report_id, coverage_id=None):
    '''
    sets report as published in a coverage; the coverage_id can be either _id or uuid
    '''
    if not db:
        return (False, 'inner application error')

    report_id = _get_id_value(report_id)
    report_get = get_report_by_id(db, report_id)
    if not report_get[0]:
        return (False, 'report not found')
    report = report_get[1]

    if 'coverages' not in report:
        coverages = {}
        for cov_set in COVERAGE_SETS:
            coverages[cov_set] = []
        update_report_set(db, report_id, {'coverages': coverages})
        report['coverages'] = coverages

    coverages = report['coverages']
    if type(coverages) is not dict:
        return (False, 'report coverages not a dict')

    for cov_set in COVERAGE_SETS:
        if (cov_set not in coverages) or (type(coverages[cov_set]) is not list):
            return (False, 'report coverage parts missing or wrong')

    to_publish = coverages['targeting']

    if coverage_id:
        coverage_uuid = None

        coverage_id = _get_id_value(coverage_id)
        if type(coverage_id) is ObjectId:
            coverage_get = get_coverage_by_id(db, coverage_id)
        else:
            coverage_uuid = coverage_id
            coverage_get = get_coverage_by_uuid(db, coverage_uuid)
        if not coverage_get[0]:
            return (False, 'coverage not found')

        if not coverage_uuid:
            # here we know the coverage_id was _id of an existent coverage
            coverage_got = coverage_get[1]
            if ('uuid' in coverage_got) and coverage_got['uuid']:
                coverage_uuid = coverage_got['uuid']
            else:
                coverage_uuid = str(uuid.uuid4().hex)
                update_coverage_set({'_id': coverage_id}, {'uuid': coverage_uuid})

        to_publish = [coverage_uuid]

    cov_published = coverages['published']
    cov_outgested = coverages['outgested']

    set_published = False
    set_outgested = False

    if not to_publish:
        return (False, 'no coverage to be published in')

    for one_cov in to_publish:
        if one_cov not in cov_published:
            set_published = True
            cov_published.append(one_cov)
        if one_cov not in cov_outgested:
            set_outgested = True
            cov_outgested.append(one_cov)

    if set_published:
        update_report_set(db, report_id, {'coverages.published': cov_published})
    if set_outgested:
        update_report_set(db, report_id, {'coverages.outgested': cov_outgested})

    timepoint = datetime.datetime.utcnow()
    adjective_set = {
        FIELD_UPDATED: timepoint,
        'proto': False,
    }
    if FIELD_UUID not in report:
        adjective_set[FIELD_UUID] = str(uuid.uuid4().hex)
    update_report_set(db, report_id, adjective_set)

    return (True, {'_id': report_id})

def do_unpublish_one(db, report_id, coverage_id=None):
    '''
    sets report as unpublished in a coverage; the coverage_id can be either _id or uuid
    '''
    if not db:
        return (False, 'inner application error')

    report_id = _get_id_value(report_id)
    report_get = get_report_by_id(db, report_id)
    if not report_get[0]:
        return (False, 'report not found')
    report = report_get[1]

    if 'coverages' not in report:
        coverages = {}
        for cov_set in COVERAGE_SETS:
            coverages[cov_set] = []
        update_report_set(db, report_id, {'coverages': coverages})
        report['coverages'] = coverages

    coverages = report['coverages']
    if type(coverages) is not dict:
        return (False, 'report coverages not a dict')

    if ('published' not in coverages) or (type(coverages['published']) is not list):
        return (False, 'published coverages missing or wrong in report')

    cov_published = []

    if coverage_id:
        coverage_uuid = None

        coverage_id = _get_id_value(coverage_id)
        if type(coverage_id) is ObjectId:
            coverage_get = get_coverage_by_id(db, coverage_id)
            if coverage_get[0] and ('uuid' in coverage_get[1]) and coverage_get[1]['uuid']:
                coverage_uuid = coverage_get[1]['uuid']
        else:
            coverage_uuid = coverage_id

        curr_specifiers = [coverage_id]
        if coverage_uuid:
            curr_specifiers.append(coverage_uuid)

        was_published = False
        for one_spec in curr_specifiers:
            if (coverage_id in coverages['published']):
                was_published = True
                break
        if not was_published:
            return (False, 'not published into the coverage')

        for one_cov in coverages['published']:
            if one_cov and (one_cov != coverage_id) and (one_cov != coverage_uuid):
                cov_published.append(one_cov)

    update_report_set(db, report_id, {'coverages.published': cov_published})

    timepoint = datetime.datetime.utcnow()
    adjective_set = {
        FIELD_UPDATED: timepoint,
        'proto': False,
    }
    update_report_set(db, report_id, adjective_set)

    return (True, {'_id': report_id})

def do_on_behalf_of(db, report_id, user_id=None):
    '''
    un/sets report as on behalf of user
    '''
    if not db:
        return (False, 'inner application error')

    report_id = _get_id_value(report_id)
    report_get = get_report_by_id(db, report_id)
    if not report_get[0]:
        return (False, 'report not found')
    report = report_get[1]

    if user_id:
        user_id = _get_id_value(user_id)

    timepoint = datetime.datetime.utcnow()
    properties_set = {
        FIELD_UPDATED: timepoint,
        'proto': False,
    }
    removal_set = None

    if user_id:
        properties_set['on_behalf_id'] = user_id
    else:
        removal_set = {'on_behalf_id': ''}

    update_report_set(db, report_id, properties_set, removal_set)

    return (True, {'_id': report_id})

