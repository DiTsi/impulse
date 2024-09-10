import json
import uuid


def gen_uuid(data):
    return uuid.uuid5(uuid.NAMESPACE_OID, json.dumps(data))
