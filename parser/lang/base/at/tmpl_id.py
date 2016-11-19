import uuid
import parser.spare


@parser.spare.at(name='id', namespace='specs')
@parser.spare.constructable
def at_id(body, *args, **kwargs):
    id_v = body.pop('@id')
    if id_v is not None:
        body["id"] = "$PARENT::" + id_v
    else:
        body["id"] = "$PARENT::" + str(uuid.uuid1())
