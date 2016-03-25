#!/usr/bin/python
# -*- #coding: utf8 -*-


class GraphComparator(object):
    def __init__(self, d1, d2, node_hash_fcn):
        self.__d1 = d1
        self.__d2 = d2
        self.__node_hash_fcn = node_hash_fcn

        self.__d1_nodes_hashs = dict(
            map(
                lambda n:
                    (self.__node_hash_fcn(n), n),
                self.__d1['nodes']
            )
        )

        self.__d2_nodes_hashs = dict(
            map(
                lambda n:
                    (self.__node_hash_fcn(n), n),
                self.__d2['nodes']
            )
        )

        self.__d1_uniq2hashs = dict(
            map(
                lambda (h, n):
                    (n['uniq'], h),
                self.__d1_nodes_hashs.items()
            )
        )

        self.__d2_uniq2hashs = dict(
            map(
                lambda (h, n):
                    (n['uniq'], h),
                self.__d2_nodes_hashs.items()
            )
        )

        self.__d1_edges_hashs = set(
            map(
                lambda e:
                    hash(
                        (
                            self.__d1_uniq2hashs[e['from']],
                            self.__d1_uniq2hashs[e['to']]
                        )
                    ),
                self.__d1['edges']
            )
        )

        self.__d2_edges_hashs = set(
            map(
                lambda e:
                    hash(
                        (
                            self.__d2_uniq2hashs[e['from']],
                            self.__d2_uniq2hashs[e['to']]
                        )
                    ),
                self.__d2['edges']
            )
        )

    def __xpath_get(d, path):
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

    def nodes_presence(self):
        if len(self.__d1['nodes']) != len(self.__d2['nodes']):
            return False
        for n1 in self.__d1['nodes']:
            h1 = self.__node_hash_fcn(n1)
            if not self.__d2_nodes_hashs.has_key(h1):
                return False
        return True

    def nodes_equality(self, xpaths):
        for n1 in self.__d1['nodes']:
            h1 = self.__node_hash_fcn(n1)
            n2 = self.__d2_nodes_hashs[h1]
            if not self.__node_xpaths_cmp(n1, n2, xpaths):
                return False
        return True

    def linkage(self):
        return self.__d1_edges_hashs == self.__d2_edges_hashs
