#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import collections
import parser.spare.wordform
import parser.engine.entries


def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in list(obj.items()):
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif isinstance(obj, list):
        return [todict(v, classkey) for v in obj]
    else:
        return str(obj)


class Link(object):
    def __init__(self, master, slave, details):
        self.__uniq = str(uuid.uuid1())
        self.__master = master.get_uniq()
        self.__slave = slave.get_uniq()
        self.__details = details

    def get_uniq(self):
        return self.__uniq

    def get_csum(self):
        return '{0}{1}'.format(self.__master, self.__slave)

    def get_master(self):
        return self.__master

    def get_slave(self):
        return self.__slave

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        raise ValueError('Unsupported fmt {0}'.format(fmt))

    def __format_dict(self):
        return {
            '__type': str(type(self)),
            'uuid': self.get_uniq(),
            'data': todict(self.__details),
        }


class MatchedEntry(object):
    def __init__(self, me, rtme=None):
        if isinstance(me, MatchedEntry):
            self.__init_from_me(me, rtme)
        else:
            self.__init_from_rtme(me)

    def __init_from_rtme(self, rtme):
        self.__form = rtme.get_form().copy({'ro', })
        self.__name = rtme.get_name()
        self.__reliability = rtme.get_reliability()
        self.__is_hidden = not rtme.get_spec().add_to_seq()
        self.__is_virtual = isinstance(
            rtme,
            parser.engine.entries.RtVirtualEntry
        )
        self.__rules = [mr.rule for mr in rtme.get_matched_rules()]
        self.__is_anchor = rtme.get_spec().is_anchor()
        self.__masters = []
        self.__slaves = []
        self.__masters_csum = set()
        self.__slaves_csum = set()

    def __init_from_me(self, me, rtme):
        assert rtme is not None
        self.__form = me.__form.copy({'ro', })
        self.__name = me.__name
        self.__reliability = me.__reliability
        self.__is_hidden = me.__is_hidden
        self.__is_virtual = me.__is_virtual
        self.__rules = [r for r in me.__rules]
        self.__is_anchor = me.__is_anchor and rtme.get_spec().is_anchor()
        if me.__is_anchor:
            self.__rules += [mr.rule for mr in rtme.get_matched_rules()]
        self.__masters = []
        self.__slaves = []
        self.__masters_csum = set()
        self.__slaves_csum = set()

    def get_name(self):
        return self.__name

    def get_form(self):
        return self.__form

    def get_links(self, hidden=False):
        return self.__links

    def get_uniq(self):
        return self.__form.get_uniq()

    def is_hidden(self):
        return self.__is_hidden

    def is_anchor(self):
        return self.__is_anchor

    def is_virtual(self):
        return self.__is_virtual

    def get_reliability(self):
        return self.__reliability

    def add_link(self, link):
        assert isinstance(link, Link)
        assert self.get_uniq() in [link.get_master(), link.get_slave()]
        if link.get_master() == self.get_uniq():
            self.__slaves.append(link)
            self.__slaves_csum.add(link.get_uniq())
        else:
            self.__masters.append(link)
            self.__masters_csum.add(link.get_uniq())

    def get_masters(self):
        return [l.get_from() for l in self.__masters]

    def get_slaves(self):
        return [l.get_to() for l in self.__slaves]

    def get_rules(self):
        return self.__rules

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        raise ValueError('unsupported format {0}'.format(fmt))

    def __format_dict(self):
        static_rules = []
        dynamic_rules = []
        for r in self.get_rules():
            if r.is_static():
                if not self.is_virtual():
                    static_rules.append(r.format('dict'))
                else:
                    static_rules.append(str(r))
            else:
                dynamic_rules.append(r.format('dict'))
        rules = collections.OrderedDict(
            [(k, v) for k, v in [
                ('stateless', static_rules),
                ('dynamic', dynamic_rules),
            ] if v
            ]
        )
        data = collections.OrderedDict(
            [(k, v) for k, v in [
                ('name', str(self.__name)),
                ('word', self.__form.get_word()),
                ('form', self.__form.format('dict-public')),
                ('rules', rules),
                ('position', self.__form.get_position()),
                ('reliability', self.__reliability),
                ('hidden', self.__is_hidden),
                ('virtual', self.__is_virtual),
                ('anchor', self.__is_anchor),
            ] if v is not None and (v or isinstance(v, int))
            ]
        )
        return {
            '__type': str(type(self)),
            'uuid': self.get_uniq(),
            'data': data,
        }


class MatchedSequence(object):
    def __init__(self, sq):
        self.__name = sq.get_rule_name()
        self.__entries = []
        self.__all_entries = []
        self.__anchors = []
        self.__links = []
        self.__all_links = []
        self.__entries_csum = set()
        self.__links_csum = set()
        self.__uid2me = {}
        self.__reliability = 1.0

        for e in sq.get_entries(hidden=True):
            me = MatchedEntry(e)
            self.__append_entries(me)
            self.__reliability *= me.get_reliability()

        for master, slaves in list(sq.get_links().items()):
            for slave, details in list(slaves.items()):
                self.__mk_link(master, slave, details)

    def __mk_link(self, master, slave, details):
        accepted_types = (parser.engine.entries.RtMatchEntry,
                          parser.engine.entries.RtVirtualEntry,
                          parser.engine.entries.RtSiblingLeaderEntry,
                          parser.engine.entries.ForeignAnchorEntry,
                          parser.engine.entries.ForeignEntry)
        assert all((
            isinstance(master, accepted_types),
            isinstance(slave, accepted_types),
            isinstance(details, list)
        )), '{0}, {1}, {2}'.format(type(master), type(slave), type(details))
        me_from = self.__uid2me[master.get_form().get_uniq()]
        me_to = self.__uid2me[slave.get_form().get_uniq()]
        l = Link(me_from, me_to, details)
        me_from.add_link(l)
        me_to.add_link(l)
        self.__append_links(me_from, me_to, l)

    def __append_entries(self, me):
        self.__all_entries.append(me)
        if not me.is_hidden():
            self.__entries.append(me)
        if me.is_anchor():
            self.__anchors.append(me)
        self.__uid2me[me.get_uniq()] = me
        if not me.is_hidden() and not me.is_virtual():
            self.__entries_csum.add(me.get_uniq())

    def __append_links(self, me_from, me_to, link):
        # assert not self.__link_exists(me_from, me_to)
        if not me_from.is_hidden() and not me_to.is_hidden():
            self.__links.append(link)
        self.__all_links.append(link)
        self.__links_csum.add(link.get_csum())

    def __link_exists(self, me_from, me_to):
        from_uniq = me_from.get_uniq()
        to_uniq = me_to.get_uniq()
        for l in self.__all_links:
            if l.get_master() == from_uniq and l.get_slave() == to_uniq:
                return True
        return False

    def get_name(self):
        return self.__name

    def get_entries(self, hidden=False, virtual=True):
        if virtual:
            return self.__all_entries if hidden else self.__entries
        return list(filter(
            lambda e: not e.is_virtual(),
            self.__all_entries if hidden else self.__entries
        ))

    def get_links(self, hidden=False):
        return self.__all_links if hidden else self.__links

    def get_entry_count(self, hidden=False, virtual=True):
        return len(self.get_entries(hidden=hidden, virtual=virtual))

    def get_reliability(self):
        return self.__reliability

    def format(self, fmt):
        if fmt == 'str':
            return self.__format_str()
        elif fmt == 'dict':
            return self.__format_dict()
        raise RuntimeError('Unsupported format {0}'.format(fmt))

    def __format_str(self):
        res = '{0} <'.format(self.get_name())
        for e in self.__all_entries:
            f = e.get_form()
            t = f.get_word()
            if e.is_virtual():
                t = '{{{0}}}'.format(t)
            if e.is_hidden():
                t = '({0})'.format(t)
            res += t + ' '
        res += '>'
        return res

    def __format_dict(self):
        nodes, links = self.__nodes_and_links()
        return {
            '__fmt_scheme': 'dg',
            '__fmt_hint': 'graph',
            '__style_hint': 'sequence',
            'nodes': nodes,
            'groups': [],
            'links': links
        }

    def __nodes_and_links(self):
        nodes = []
        links = []
        for e in self.__entries:
            nodes.append(e.format('dict'))

        for l in self.__links:
            nodes.append(l.format('dict'))

            links.append({
                'from': l.get_master(),
                'to': l.get_uniq(),
                'single2single': True
            })
            links.append({
                'from': l.get_uniq(),
                'to': l.get_slave(),
                'single2single': True
            })

        return nodes, links

    def __repr__(self):
        r = "MatchedSequence(objid={0}, entries=[{1}])".format(
            hex(id(self)),
            ', '.join(map(lambda x: x.get_form().get_word(), self.__entries))
        )
        return r.encode('utf-8')

    def __str__(self):
        return "MatchedSequence(objid={0})".format(hex(id(self)))

    def __eq__(self, other):
        assert isinstance(other, MatchedSequence)
        if id(self) == id(other):
            return True
        return all((self.__entries_csum == other.__entries_csum,
                    self.__links_csum == other.__links_csum,))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(
            (
                tuple(sorted([str(i) for i in self.__entries_csum])),
                tuple(sorted(self.__links_csum))
            )
        )
