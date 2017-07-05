import parser.spare


@parser.spare.at(name='interleaved', namespace='specs')
@parser.spare.constructable
def interleaved(body, *args, **kwargs):
    members = body.pop('@interleaved')
    body['interleaved'] = {
        "order": "equal",
        "members": members
    }
