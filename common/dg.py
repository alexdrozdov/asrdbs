import uuid


class BaseNode(object):
    """Base class to inherit any semi-graph node structures

    Class is used as base class and provides some api required for graph and
    subgraph creation inside th dg module"""

    def __init__(self):
        self.__uuid = uuid.uuid1()


class SingleNode(BaseNode):
    """Base class for nodes that represents singilar objects

    Any object derived from this class will be transformed into a sigle graph
    node.
    Compare to MultiNode that represents group of singilar objects."""

    def __init__(self):
        super().__init__()

    def get_slaves(self):
        raise NotImplemented()


class MultiNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.__objects = set()

    def get_objects(self):
        raise NotImplemented()


class SingleNodeRef(object):
    def __init__(self, obj, n2id):
        self.__obj = obj
        self.__uuid, self.__owner = self.__get_uuid(obj, n2id)
        self.__slaves = [self.__get_uuid(s, n2id)[0] for s in obj.get_slaves()]

    def __get_uuid(self, obj, n2id, owner=None):
        if owner is not None:
            owner, _ = self.__get_uuid(owner, n2id)
        if id(obj) not in n2id:
            n2id[id(obj)] = (str(uuid.uuid1()), owner)
        return n2id[id(obj)]

    def get_uniq(self):
        return self.__uuid

    def get_slaves(self):
        return self.__slaves

    def get_owner(self):
        return self.__owner

    def get_obj(self):
        return self.__obj


class MultiNodeRef(object):
    def __init__(self, obj, n2id):
        self.__obj = obj
        self.__uuid, self.__owner = self.__get_uuid(obj, n2id, None)
        self.__objects = [
            self.__get_uuid(o, n2id, obj)[0]
            for o in obj.get_objects()
        ]

    def __get_uuid(self, obj, n2id, owner=None):
        if owner is not None:
            owner, _ = self.__get_uuid(owner, n2id)
        if id(obj) not in n2id:
            n2id[id(obj)] = (str(uuid.uuid1()), owner)
        return n2id[id(obj)]

    def get_uniq(self):
        return self.__uuid

    def get_obj(self):
        return self.__obj

    def get_objects(self):
        return self.__objects


class Subgraph(object):
    def __init__(self, name, nodes, links):
        self.__name = name
        self.__nodes = nodes
        self.__links = links

    def get_name(self):
        return self.__name

    def format(self, fmt):
        if fmt == 'dict':
            return self.__to_dict()
        raise RuntimeError('Not supported format {0}'.format(fmt))

    def __to_dict(self):
        return {
            '__fmt_scheme': 'dg',
            '__fmt_hint': 'graph',
            '__style_hint': 'selectors',
            'nodes': self.__nodes_to_dict(True),
            'groups': self.__nodes_to_dict(False),
            'links': self.__links_to_dict()
        }

    def __links_to_dict(self):
        return self.__links

    def __nodes_to_dict(self, single=True):
        res = []
        for v in self.__nodes.values():
            if single and isinstance(v, SingleNodeRef):
                res.append(self.__single_to_dict(v))
            if not single and isinstance(v, MultiNodeRef):
                res.append(self.__multi_to_dict(v))
        return res

    def __single_to_dict(self, v):
        return {
            'uuid': v.get_uniq(),
            'slaves': v.get_slaves(),
            'data': v.get_obj().format('dict')
        }

    def __multi_to_dict(self, v):
        return {
            'uuid': v.get_uniq(),
            'objects': v.get_objects(),
            'data': v.get_obj().format('dict')
        }

    @staticmethod
    def from_node(node):
        name = uuid.uuid1()

        if hasattr(node, 'get_name'):
            name = node.get_name()
        elif hasattr(node, 'get_tag'):
            name = node.get_tag()

        nodes = Subgraph.__node_subset(node)
        links = Subgraph.__subset_links(nodes)
        return Subgraph(name, nodes, links)

    @staticmethod
    def __subset_links(nodes):
        links = []
        for n in nodes.values():
            if not isinstance(n, SingleNodeRef):
                continue
            for s in n.get_slaves():
                s = nodes[s]
                if isinstance(s, SingleNodeRef):
                    links.append(
                        {
                            'from': n.get_uniq(),
                            'to': s.get_uniq(),
                            'single2single': True
                        }
                    )
                elif isinstance(s, MultiNodeRef):
                    links.append(
                        {
                            'from': n.get_uniq(),
                            'to': s.get_uniq(),
                            'single2single': False
                        }
                    )
                else:
                    raise RuntimeError('{0} doesnt match neither SingleNodeRef'
                                       'nor MultiNodeRef'.format(s))
        return links

    @staticmethod
    def __node_subset(node):
        nodeset = set()
        unprocessed = set([node, ])
        n2id = {}
        objects = {}
        while unprocessed:
            node = unprocessed.pop()
            nodeset.add(node)
            if isinstance(node, SingleNode):
                nr = SingleNodeRef(node, n2id)
                for s in node.get_slaves():
                    if s in nodeset or s in unprocessed:
                        continue
                    unprocessed.add(s)
            elif isinstance(node, MultiNode):
                nr = MultiNodeRef(node, n2id)
                for o in node.get_objects():
                    unprocessed.add(o)
            else:
                raise RuntimeError(
                    'Node {0} doesnt inherit neither SingleNode nor MultiNode'
                    ''.format(node)
                )
            objects[nr.get_uniq()] = nr
        return objects
