import os
import json


import parser
import common.dictcmp


class MatchResCmp(common.dictcmp.GraphCmp):
    def __init__(self, d):
        cfg = parser.config()
        self.__node_attributes = cfg['/tests/parser/compare']
        super().__init__(d)

    def node_hash(self, n):
        t = n['__type']
        if 'MatchedEntry' in t:
            return hash((
                n['data']['position'],
                # n['data']['word'],
                n['data']['name'] if 'virtual' in n['data'] and n['data']['virtual'] else '',
            ))
        else:
            raise ValueError('unsupported node type {0}'.format(t))

    def node_ignore(self, n):
        data = n['data']
        if 'hidden' in data:
            return data['hidden']
        return False

    def node_is_reference(self, n):
        t = n['__type']
        return 'MatchedEntry' in t

    def node_is_connection(self, n):
        t = n['__type']
        return 'MatchedEntry' not in t

    def node_attributes(self):
        return self.__node_attributes

    def __eq__(self, other):
        if not isinstance(other, MatchResCmp):
            other = MatchResCmp(other)
        return super(MatchResCmp, self).__eq__(other)


class CrossMatchResCmp(object):
    def __init__(self, obj):
        assert isinstance(obj, list)
        self.__obj = obj
        self.__cmps = [MatchResCmp(o) for o in self.__obj]

    def __eq__(self, other):
        if not isinstance(other, CrossMatchResCmp):
            other = CrossMatchResCmp(other)
        if len(self.__obj) != len(other.__obj):
            return False
        for i, c in enumerate(self.__cmps):
            for j, cc in enumerate(other.__cmps):
                if c == cc:
                    break
            else:
                return False
            continue
        return True


def from_fs(base_dir):
    files = [f for f in os.listdir(base_dir) if f.endswith('.json')]
    objs = []
    for fn in files:
        with open(os.path.join(base_dir, fn)) as f:
            objs.append(json.load(f))
    return CrossMatchResCmp(objs)


def compare(obj1, obj2):
    cmrc_1 = CrossMatchResCmp(obj1) if not isinstance(obj1, CrossMatchResCmp) else obj1
    cmrc_2 = CrossMatchResCmp(
        [o.format('dict') for o in obj2]
    ) if not isinstance(obj2, CrossMatchResCmp) else obj2
    return cmrc_1 == cmrc_2
