#!/usr/bin/python
# -*- #coding: utf8 -*-


from argparse import Namespace as ns


class GraphCmp(object):
    def __init__(self, d, node_hash_fcn, filter_fcn=None, xpaths=None):
        self.__d = d
        self.__node_hash_fcn = node_hash_fcn
        self.__filter_fcn = filter_fcn if filter_fcn is not None else self.__true
        self.__xpaths = xpaths

        self.__d_nodes_hashs = dict(
            map(
                lambda n:
                (self.__node_hash_fcn(n), n),
                filter(
                    self.__filter_fcn,
                    self.__d['nodes']
                )
            )
        )

        self.__d_uniq2hashs = dict(
            map(
                lambda (h, n):
                    (n['uniq'], h),
                self.__d_nodes_hashs.items()
            )
        )

        self.__d_edges_hashs = set(
            map(
                lambda e:
                    hash(
                        (
                            self.__d_uniq2hashs[e['from']],
                            self.__d_uniq2hashs[e['to']]
                        )
                    ),
                self.__d['edges']
            )
        )

    def __true(self, *args):
        return True

    def __xpath_get(self, d, path):
        elem = d
        try:
            for x in path.strip("/").split("/"):
                try:
                    x = int(x)
                    elem = elem[x]
                except ValueError:
                    elem = elem.get(x)
        except:
            return None
        return elem

    def __node_xpaths_cmp(self, n1, n2, xpaths):
        for xpath in xpaths:
            v1 = self.__xpath_get(n1, xpath)
            v2 = self.__xpath_get(n2, xpath)
            if v1 is None and v2 is None:
                continue
            if v1 != v2:
                return False
        return True

    def nodes_presence(self, other):
        if len(self.__d['nodes']) != len(other.__d['nodes']):
            return False
        for n1 in self.__d['nodes']:
            if not self.__filter_fcn(n1):
                continue
            h1 = self.__node_hash_fcn(n1)
            if not other.__d_nodes_hashs.has_key(h1):
                return False
        return True

    def nodes_equality(self, other):
        for n1 in self.__d['nodes']:
            if not self.__filter_fcn(n1):
                continue
            h1 = self.__node_hash_fcn(n1)
            n2 = other.__d_nodes_hashs[h1]
            if not self.__node_xpaths_cmp(n1, n2, self.__xpaths):
                return False
        return True

    def linkage(self, other):
        return self.__d_edges_hashs == other.__d_edges_hashs

    def compare(self, other):
        return ns(
            res=self.nodes_presence(other) and self.linkage(other) and self.nodes_equality(self)
        )

    def __eq__(self, other):
        return self.compare(other).res
