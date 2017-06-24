#!/usr/bin/python
# -*- #coding: utf8 -*-


from argparse import Namespace as ns


class GraphCmp(object):
    def __init__(self, d):
        self.__d = d
        self.__eval_node_hashes()
        self.__eval_edge_hashes()

    def __eval_node_hashes(self):
        references = [n for n in self.__d['nodes']
                      if self.node_is_reference(n) and not self.node_ignore(n)
                      ]
        connections = [n for n in self.__d['nodes']
                       if self.node_is_connection(n) and not self.node_ignore(n)
                       ]

        self.__d_nodes_hashs = {self.node_hash(n): n for n in references}
        self.__d_uniq2hashs = {n['uuid']: h
                               for h, n in self.__d_nodes_hashs.items()}
        while connections:
            n = connections.pop(0)
            froms, tos = self.__find_fromtos(n)
            if not self.__known_uuids(froms + tos):
                connections.append(n)
                continue
            froms = [self.__d_uniq2hashs[f] for f in froms]
            tos = [self.__d_uniq2hashs[t] for t in tos]
            seed = str(sorted(froms) + [None, ] + sorted(tos))
            new_hash = hash(seed)
            self.__d_nodes_hashs[new_hash] = n
            self.__d_uniq2hashs[n['uuid']] = new_hash

    def __find_fromtos(self, n):
        uid = n['uuid']
        froms = []
        tos = []
        for e in self.__d['links']:
            if e['from'] == uid:
                tos.append(e['to'])
            if e['to'] == uid:
                froms.append(e['from'])
        return froms, tos

    def __known_uuids(self, uuids):
        for uid in uuids:
            if uid not in self.__d_uniq2hashs:
                return False
        return True

    def __eval_edge_hashes(self):
        self.__d_edges_hashs = set(
            [hash(
                (
                    self.__d_uniq2hashs[e['from']],
                    self.__d_uniq2hashs[e['to']]
                )
            ) for e in self.__d['links']]
        )

    def node_hash(self, n):
        raise RuntimeError('not implemented')

    def node_ignore(self, n):
        return False

    def node_is_reference(self, n):
        return True

    def node_is_connection(self, n):
        return False

    def node_attributes(self):
        raise RuntimeError('not implemented')

    def __xpath_get(self, d, path):
        elem = d
        try:
            for x in path.strip("/").split("/"):
                try:
                    x = int(x)
                    elem = elem[x]
                except ValueError:
                    e = elem.get(x)
                    if x == '*':
                        if x in elem:
                            continue
                    else:
                        elem = e
        except:
            return None
        return elem

    def __node_xpaths_cmp(self, n1, n2):
        for xpath in self.node_attributes():
            v1 = self.__xpath_get(n1, xpath)
            v2 = self.__xpath_get(n2, xpath)
            if v1 is None and v2 is None:
                continue
            if v1 != v2:
                return False
        return True

    def nodes_presence(self, other):
        my_hashes = set(self.__d_nodes_hashs)
        other_hashes = set(other.__d_nodes_hashs)
        return my_hashes == other_hashes

    def nodes_equality(self, other):
        for h, n1 in self.__d_nodes_hashs.items():
            n2 = other.__d_nodes_hashs[h]
            if not self.__node_xpaths_cmp(n1, n2):
                return False
        return True

    def linkage(self, other):
        return self.__d_edges_hashs == other.__d_edges_hashs

    def compare(self, other):
        presence = self.nodes_presence(other)
        linkage = presence and self.linkage(other)
        equality = linkage and self.nodes_equality(other)
        return ns(res=presence and linkage and equality)

    def __eq__(self, other):
        return self.compare(other).res
