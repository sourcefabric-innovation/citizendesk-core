#!/usr/bin/env python
#
# Citizen Desk
#

import datetime

try:
    unicode
except:
    unicode = str

INSECURE = True

collection = 'twt_oauths'

schema = {
    '_id': 1,
    'spec': {
        'consumer_key': 'YOUR TWITER Consumer key',
        'consumer_secret': 'YOUR TWITER Consumer secret',
        'access_token_key': 'YOUR TWITER Access token',
        'access_token_secret': 'YOUR TWITER Access token secret'
    },
    'logs': {
        'created': '2014-03-12T12:00:00',
        'updated': '2014-03-12T12:00:00'
    }
}

def do_get_one(db, doc_id):
    '''
    returns data of a single oauth spec
    '''
    if not db:
        return (False, 'inner application error')

    if doc_id is not None:
        if doc_id.isdigit():
            try:
                doc_id = int(doc_id)
            except:
                pass

    coll = db[collection]
    doc = coll.find_one({'_id': doc_id})

    if not doc:
        return (False, 'oauth spec not found')

    if INSECURE:
        try:
            for key in doc['spec']:
                if doc['spec'][key]:
                    doc['spec'][key] = '****' + str(doc['spec'][key])[-4:]
        except:
            pass

    return (True, doc)

def do_get_list(db, offset=0, limit=20):
    '''
    returns data of a set of oauth specs
    '''
    if not db:
        return (False, 'inner application error')

    coll = db[collection]
    cursor = coll.find()
    if offset:
        cursor = cursor.skip(offset)
    if limit:
        cursor = cursor.limit(limit)

    docs = []
    for entry in cursor:
        if not entry:
            continue
        if INSECURE:
            try:
                for key in entry['spec']:
                    if entry['spec'][key]:
                        entry['spec'][key] = '****' + str(entry['spec'][key])[-4:]
            except:
                pass

        docs.append(entry)

    return (True, docs)

def _check_schema(doc):

    for key in schema['spec']:
        if key not doc:
            return (False, '"' + str(key) + '" is missing in the data spec')
        if doc[key] is None:
            continue
        if type(doc[key]) not in [str, unicode]:
            return (False, '"' + str(key) + '" field has to be string')
    return True

def do_post_one(db, doc_id=None, data=None):
    '''
    sets data of a single oauth spec
    '''
    if not db:
        return (False, 'inner application error')

    if data is None:
        return (False, 'data not provided')

    if ('spec' not in data) or (type(data['spec']) is not dict):
        return (False, '"spec" part not provided')
    spec = data['spec']

    if doc_id is not None:
        if doc_id.isdigit():
            try:
                doc_id = int(doc_id)
            except:
                pass

    coll = db[collection]

    timepoint = datetime.datetime.utcnow()
    created = timepoint
    updated = timepoint

    if doc_id is not None:
        entry = coll.find_one({'_id': doc_id})
        if not entry:
            return (False, '"filter" of the provided _id not found')
        try:
            if ('logs' in entry) and (entry['logs']) and ('created' in entry['logs']):
                if entry['logs']['created']:
                    created = entry['logs']['created']
        except:
            created = timepoint

    doc = {
        'logs': {
            'created': created,
            'updated': updated
        },
        'spec': {}
    }

    for key in schema['spec']:
        doc['spec'][key] = None
        if key in spec:
            doc['spec'][key] = spec[key]

    res = _check_schema(doc['spec'])
    if not res[0]:
        return res

    if not doc_id:
        try:
            entry = db['counters'].find_and_modify(query={'_id': collection}, update={'$inc': {'next':1}}, new=True, upsert=True, full_response=False);
            doc_id = entry['next']
        except:
            return (False, 'can not create document id')

    doc['_id'] = doc_id

    doc_id = coll.save(doc)

    return (True, {'_id': doc_id})

def do_delete_one(db, doc_id):
    '''
    deletes data of a single oauth spec
    '''
    if not db:
        return (False, 'inner application error')

    coll = db[collection]

    coll.remove({'_id': doc_id})

    return (True, {'_id': doc_id})

