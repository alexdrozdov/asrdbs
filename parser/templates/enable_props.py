#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import parser.spare
from parser.lang.sdefs import TermPropsSpecs


def mk_enableprops_tag():
    return '#-enable-props' + str(uuid.uuid1())


@parser.spare.at(name='enable-props', namespace='selectors')
@parser.spare.constructable
def enable_props(body, *args, **kwargs):
    ep = body.pop('@enable-props')
    body['enable-props'] = [TermPropsSpecs().Enable(ep), ]
    if 'tag' not in body and '@tag' not in body:
        body['tag'] = mk_enableprops_tag()
