#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import json
import parser.wordform
import parser.engine.entries
from common.linewrapper import LineWrapper


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

    def get_details(self):
        return self.__details

    def get_master(self):
        return self.__master

    def get_slave(self):
        return self.__slave

    def export_dict(self):
        return {
            'from': self.__master,
            'to': self.__slave,
            'udata': todict(self.__details),
        }

    def format(self, fmt):
        if fmt == 'dict':
            return self.export_dict()
        if fmt == 'dot-html-table':
            return self.__fmt_dot_html_table()
        raise ValueError('Unsupported fmt {0}'.format(fmt))

    def __fmt_dot_html_table(self):
        lw = LineWrapper(60, 70, [' ', '::'], 4, False)
        s = '<TABLE CELLSPACING="0">'
        s += '<TH><TD BGCOLOR="darkseagreen1"><FONT FACE="ARIAL">{0}</FONT></TD></TH>'.format(
            self.get_uniq()
        )
        s += '<TR><TD BGCOLOR="darkseagreen1"><FONT FACE="ARIAL">master: {0}</FONT></TD></TR>'.format(
            self.get_master()
        )
        s += '<TR><TD BGCOLOR="darkseagreen1"><FONT FACE="ARIAL">slave: {0}</FONT></TD></TR>'.format(
            self.get_slave()
        )

        for d in self.get_details():
            s += '<TR><TD BGCOLOR="darkseagreen1"><FONT FACE="ARIAL">{0}</FONT></TD></TR>'.format(
                self.__format_dot_html_dict(d, lw)
            )
        s += '</TABLE>'
        return s

    def __format_dot_html_dict(self, d, line_wrapper):
        s = '<TABLE CELLSPACING="0">'
        row_fmt = ('<TR>'
                   '<TD {align} {valign} {bgcolor}>{k}</TD>'
                   '<TD {align} {valign} {bgcolor}>{v}</TD>'
                   '</TR>')
        align = 'ALIGN="LEFT"'
        valign = 'VALIGN="TOP"'
        bgcolor = 'BGCOLOR="WHITE"'
        for k, v in list(d.items()):
            if isinstance(v, dict) and v:
                v_str = self.__format_dot_html_dict(v, line_wrapper)
            elif isinstance(v, list) and v:
                v_str = self.__format_dot_html_list(v, line_wrapper)
            else:
                v_str = line_wrapper.wrap(
                    str(v),
                    linebreak='<BR/>',
                    indent_char='&nbsp;'
                )
            s += row_fmt.format(
                align=align,
                valign=valign,
                bgcolor=bgcolor,
                k=k,
                v=v_str
            )
        s += '</TABLE>'
        return s

    def __format_dot_html_list(self, l, line_wrapper):
        s = '<TABLE CELLSPACING="0">'
        row_fmt = ('<TR>'
                   '<TD {align} {valign} {bgcolor}>{v}</TD>'
                   '</TR>')
        align = 'ALIGN="LEFT"'
        valign = 'VALIGN="TOP"'
        bgcolor = 'BGCOLOR="WHITE"'
        for v in l:
            if isinstance(v, dict) and v:
                v_str = self.__format_dot_html_dict(v, line_wrapper)
            elif isinstance(v, list) and v:
                v_str = self.__format_dot_html_list(v, line_wrapper)
            else:
                v_str = line_wrapper.wrap(
                    str(v),
                    linebreak='<BR/>',
                    indent_char='&nbsp;'
                )
            s += row_fmt.format(
                align=align,
                valign=valign,
                bgcolor=bgcolor,
                v=v_str
            )
        s += '</TABLE>'
        return s


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

    def export_dict(self):
        return {
            'uniq': self.get_uniq(),
            'udata': {
                'name': str(self.__name),
                'position': self.__form.get_position(),
                'word': self.__form.get_word(),
                'reliability': self.__reliability,
                'hidden': self.__is_hidden,
                'virtual': self.__is_virtual,
                'anchor': self.__is_anchor,
                'form': self.__form.format('dict-form'),
            },
        }

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

    def get_master_links(self):
        return self.__masters

    def get_slave_links(self):
        return self.__slaves

    def get_masters(self):
        return [l.get_from() for l in self.__masters]

    def get_slaves(self):
        return [l.get_to() for l in self.__slaves]

    def get_rules(self):
        return self.__rules

    def format(self, fmt):
        if fmt == 'dot-html-table':
            return self.__fmt_dot_html_table()
        if fmt == 'dict':
            return self.export_dict()
        raise ValueError('unsupported format {0}'.format(fmt))

    def __fmt_dot_html_table(self):
        s = '<TABLE CELLSPACING="0">'
        s += '<TH><TD BGCOLOR="darkseagreen1"><FONT FACE="ARIAL">{0}</FONT></TD></TH>'.format(
            self.get_name()
        )

        s += '<TR><TD BGCOLOR="darkseagreen2"><FONT FACE="ARIAL"><B>{0}: {1}</B></FONT></TD></TR>'.format(
            self.get_form().get_word(),
            self.get_form().get_position(),
        )

        s += '<TR><TD BGCOLOR="white"><FONT FACE="ARIAL">{0}</FONT></TD></TR>'.format(
            self.get_form().format('dot-html-table')
        )

        for r in self.get_rules():
            s += '<TR><TD ALIGN="LEFT" BGCOLOR="{0}"><FONT FACE="ARIAL">{1}</FONT></TD></TR>'.format(
                'darkolivegreen1' if r.is_static() else 'burlywood1',
                r.format('dot-html'))
        s += '</TABLE>'
        return s


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
            if e.has_attribute('subseq'):
                self.__copy_subseq(e)
                continue
            me = MatchedEntry(e)
            self.__append_entries(me)
            self.__reliability *= me.get_reliability()

        for master, slaves in list(sq.get_links().items()):
            for slave, details in list(slaves.items()):
                self.__mk_link(master, slave, details)

    def __copy_subseq(self, rtme):
        for me in rtme.get_attribute('subseq').get_entries(hidden=True):
            if isinstance(
                me.get_form(),
                (
                    parser.wordform.SpecStateIniForm,
                    parser.wordform.SpecStateFiniForm
                )
            ):
                continue
            me = MatchedEntry(me, rtme)
            self.__append_entries(me)
        for me in rtme.get_attribute('subseq').get_entries(hidden=True):
            if isinstance(
                me.get_form(),
                (
                    parser.wordform.SpecStateIniForm,
                    parser.wordform.SpecStateFiniForm
                )
            ):
                continue
            for link in me.get_master_links():
                master = link.get_master()
                slave = link.get_slave()
                me_from = self.__uid2me[master]
                me_to = self.__uid2me[slave]
                l = Link(me_from, me_to, link.get_details())
                me_from.add_link(l)
                me_to.add_link(l)
                self.__append_links(me_from, me_to, l)

    def __mk_link(self, master, slave, details):
        accepted_types = (parser.engine.entries.RtMatchEntry,
                          parser.engine.entries.RtVirtualEntry)
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
        assert fmt == 'str'
        res = '{0} <'.format(self.get_name())
        for e in self.__all_entries:
            f = e.get_form()
            if not e.is_hidden():
                res += '{0} '.format(f.get_word())
            else:
                res += '< {0} >'.format(f.get_word())
        res += 'reliability={0}, entries_csum={1}, links_csum={2}>'.format(
            self.get_reliability(),
            self.__entries_csum,
            self.__links_csum
        )
        return res

    def export_dict(self):
        nodes = list(map(
            lambda e: e.export_dict(),
            self.__all_entries
        ))
        edges = list(map(
            lambda l: l.export_dict(),
            self.__all_links
        ))
        return {
            'name': self.__name,
            'reliability': self.__reliability,
            'nodes': nodes,
            'edges': edges,
        }

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


class SequenceMatchRes(object):
    def __init__(self, sqs):
        self.__sqs = sqs

    def get_sequences(self):
        return self.__sqs

    def export_obj(self):
        return list(map(
            lambda s: s.export_dict(),
            self.__sqs
        ))

    def export_json(self):
        return json.dumps(
            self.export_obj()
        )
