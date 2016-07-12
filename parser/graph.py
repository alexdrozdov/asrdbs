#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import json
import traceback


class SentGraph(object):
    def __init__(self, img_type='png'):
        self.__out_type = img_type

    def generate(self, entries, outfile, subgraph=None):
        gen = SentGraphGen()
        s = gen.generate(entries, subgraph)

        tmp_file = outfile + '.tmp.graph'
        with open(tmp_file, 'w') as f:
            f.write(s.encode('utf8'))

        os.system('dot -T{0} {1} -o {2}'.format(self.__out_type, tmp_file, outfile))


class SentGraphGen(object):
    def __init__(self):
        self.__obj2id = {}
        self.__last_id = 0

    def __dict_to_istr(self, d, offset=0):
        r = u''
        if isinstance(d, unicode) or isinstance(d, str):
            d = json.loads(d)
        for k, v in d.items():
            r += u'  ' * offset + k + ': '
            if isinstance(v, list):
                r += '['
                for vv in v:
                    r += self.__dict_to_istr(vv, offset=offset+1)
                r += u'  ' * offset + ']\l'
            else:
                r += str(v) + "\l"
        return r

    def __mkid(self, iid):
        return 'obj_{0}'.format(iid)

    def __add_obj(self, obj):
        self.__obj2id[obj] = self.__mkid(self.__last_id)
        self.__last_id += 1

    def __get_obj_id(self, obj):
        return self.__obj2id[obj]

    def __gen_link_label(self, l, subgraph=None):
        if subgraph is None:
            style = "filled"
        elif subgraph.has_link(l):
            style = "filled"
        else:
            style = "invisible"
        s = u'\t{0} [label = "{1}", shape="octagon", style="{2}", fillcolor="orchid"];\r\n'.format(self.__get_obj_id(l), self.__dict_to_istr(l.get_rule().explain_str()), style)
        return s

    def __gen_links(self, form, subgraph=None):
        s = u''
        try:
            for sl in form.get_slaves():
                if subgraph is None:
                    style = "filled"
                elif subgraph.has_link(sl[1]):
                    style = "filled"
                else:
                    style = "invis"
                s += u'\t{0}->{1}->{2} [style="{3}"];\r\n'.format(self.__get_obj_id(form), self.__get_obj_id(sl[1]), self.__get_obj_id(sl[0]), style)
        except:
            print traceback.format_exc()
        return s

    def __gen_subgraph(self, e, subgraph=None):
        s = u'subgraph cluster_{0} {{\r\n'.format(self.__get_obj_id(e))
        s += u'\tnode [shape="box", style="filled", fillcolor="yellow", fontcolor="black"];\r\n'
        s += u'\tlabel = "{0}";\r\n'.format(e.get_word())
        for f in e.get_forms():
            if subgraph is None:
                style = "filled"
            elif subgraph.has_form(f):
                style = "filled"
            else:
                style = "invisible"
            s += u'\t"{0}" [label="{1}", style="{2}"];\r\n'.format(self.__get_obj_id(f), f.format_info(crlf=True), style)
        s += u'}\r\n'
        return s

    def generate(self, entries, subgraph=None):
        for e in entries:
            self.__add_obj(e)
            for f in e.get_forms():
                self.__add_obj(f)
                for l in f.get_slaves():
                    self.__add_obj(l[1])

        s = u'digraph D {\r\n'
        for e in entries:
            s += self.__gen_subgraph(e, subgraph)

        for e in entries:
            for f in e.get_forms():
                s += self.__gen_links(f, subgraph)

        for e in entries:
            for f in e.get_forms():
                for l in f.get_slaves():
                    s += self.__gen_link_label(l[1], subgraph)

        s += u'}\r\n'

        return s


class SpecGraph(object):
    def __init__(self, img_type='png'):
        self.__out_type = img_type

    def generate(self, states, outfile):
        gen = SpecGraphGen()
        s = gen.generate(states)

        tmp_file = outfile + '.tmp.graph'
        with open(tmp_file, 'w') as f:
            f.write(s.encode('utf8'))

        os.system('dot -T{0} {1} -o {2}'.format(self.__out_type, tmp_file, outfile))


class SpecGraphGen(object):
    def __init__(self):
        self.__obj2id = {}
        self.__last_id = 0

    def __mkid(self, iid):
        return 'obj_{0}'.format(iid)

    def __add_obj(self, obj):
        self.__obj2id[obj] = self.__mkid(self.__last_id)
        self.__last_id += 1

    def __get_obj_id(self, obj):
        return self.__obj2id[obj]

    def __gen_links(self, st):
        s = u''
        for trs in st.get_transitions():
            try:
                to = trs.get_to()
                style = "filled"
                n_trs = self.__get_obj_id(trs)
                n_from = self.__get_obj_id(st)
                n_to = self.__get_obj_id(to)
                s += u'\t{0}->{1}->{2} [style="{3}"];\r\n'.format(n_from, n_trs, n_to, style)
            except:
                print 'state name: {0}, trs name: {1}'.format(st.get_name(), to.get_name())
                print traceback.format_exc()
        return s

    def __gen_state(self, st):
        label = '<TABLE>'
        label += '<TR><TD BGCOLOR="darkseagreen1">{0}</TD></TR>'.format(st.get_name())
        if st.is_anchor():
            label += '<TR><TD BGCOLOR="blue">ANCHOR</TD></TR>'
        for r in st.get_rules_ro():
            label += '<TR><TD ALIGN="LEFT" BGCOLOR="{0}">{1}</TD></TR>'.format('darkolivegreen1' if r.is_static() else 'burlywood1', r.get_info(wrap=True))
        label += '<TR><TD ALIGN="LEFT">{0}</TD></TR>'.format('level: {0}'.format(st.get_level()))
        label += '<TR><TD ALIGN="LEFT">{0}</TD></TR>'.format('glevel: {0}'.format(st.get_glevel()))
        label += '</TABLE>'

        style = "filled"
        color = "white"
        if st.is_init():
            color = "yellow"
        elif st.is_fini():
            color = "orchid"
        return u'\t"{0}" [label=< {1} >, style="{2}", fillcolor="{3}"];\r\n'.format(self.__get_obj_id(st), label, style, color)

    def __gen_trs(self, trs):
        label = trs.get_levelpath()
        return u'\t"{0}" [label="{1}", style="filled"];\r\n'.format(self.__get_obj_id(trs), label)

    def generate(self, states):
        self.__trs = []
        for s in states:
            self.__add_obj(s)
            for r in s.get_rules_ro():
                self.__add_obj(r)
            for trs in s.get_transitions():
                self.__add_obj(trs)
                self.__trs.append(trs)

        s = u'digraph D {\r\n'
        for st in states:
            s += self.__gen_state(st)

        for trs in self.__trs:
            s += self.__gen_trs(trs)

        for st in states:
            s += self.__gen_links(st)

        s += u'}\r\n'

        return s


class SequenceGraph(object):
    def __init__(self, img_type='png'):
        self.__out_type = img_type

    def generate(self, sequence, outfile):
        gen = SequenceGraphGen()
        s = gen.generate(sequence)

        tmp_file = outfile + '.tmp.graph'
        with open(tmp_file, 'w') as f:
            f.write(s.encode('utf8'))

        os.system('dot -T{0} {1} -o {2}'.format(self.__out_type, tmp_file, outfile))


class GraphGen(object):
    def __init__(self):
        self.__obj2id = {}
        self.__last_id = 0

    def dict_to_istr(self, d, offset=0):
        r = u''
        if isinstance(d, unicode) or isinstance(d, str):
            d = json.loads(d)
        if isinstance(d, dict):
            r += u'  ' * offset + '{\l'
            for k, v in d.items():
                r += u'  ' * (offset + 1) + k + ':'
                if isinstance(v, list):
                    r += '\l'
                    r += self.dict_to_istr(v, offset=offset+1)
                else:
                    r += ' ' + str(v) + '\l'
            r += u'  ' * offset + '}\l'
        elif isinstance(d, list):
            r += u'  ' * offset + '[\l'
            for dd in d:
                r += self.dict_to_istr(dd, offset=offset+1)
            r += u'  ' * offset + ']\l'
        return r

    def __mkid(self, iid):
        return 'obj_{0}'.format(iid)

    def add_obj(self, obj):
        self.__obj2id[obj] = self.__mkid(self.__last_id)
        self.__last_id += 1

    def get_obj_id(self, obj):
        return self.__obj2id[obj]

    def obj_exists(self, obj):
        return self.__obj2id.has_key(obj)


class SequenceGraphGen(GraphGen):
    def __init__(self):
        super(SequenceGraphGen, self).__init__()

    def __gen_link(self, link):
        s = u'\t{0} [label = "{1}", shape="box", style="filled", fillcolor="orchid"];\r\n'.format(
            self.get_obj_id(link),
            self.dict_to_istr(link.get_details()))
        return s

    def __gen_entry(self, entry):
        label = u'<TABLE>'
        label += u'<TR><TD BGCOLOR="darkseagreen1">{0}</TD></TR>'.format(entry.get_name())

        label += u'<TR><TD BGCOLOR="darkseagreen2">{0}: {1}</TD></TR>'.format(
            entry.get_form().get_word(),
            entry.get_form().get_position(),
        )
        label += entry.get_form().format('dot-html')

        for r in entry.get_rules():
            label += u'<TR><TD ALIGN="LEFT" BGCOLOR="{0}">{1}</TD></TR>'.format(
                u'darkolivegreen1' if r.is_static() else u'burlywood1',
                r.format('dot-html'))
        label += u'</TABLE>'

        s = u'\t"{0}" [label=< {1} >, style="filled", fillcolor="white"];\r\n'.format(
            self.get_obj_id(entry.get_uniq()),
            label)
        return s

    def __link_entries(self, link):
        s = u'\t{0}->{1}->{2} [style="filled"];\r\n'.format(
            self.get_obj_id(link.get_master()),
            self.get_obj_id(link),
            self.get_obj_id(link.get_slave()))
        return s

    def generate(self, sequence):
        s = u'digraph D {\r\n'

        for e in sequence.get_entries(hidden=False):
            self.add_obj(e.get_uniq())
            s += self.__gen_entry(e)

        for l in sequence.get_links(hidden=False):
            self.add_obj(l)
            s += self.__gen_link(l)

        for l in sequence.get_links(hidden=False):
            s += self.__link_entries(l)

        s += u'}\r\n'

        return s


class SelectorGraph(object):
    def __init__(self, img_type='png'):
        self.__out_type = img_type

    def generate(self, selectors, outfile):
        gen = SelectorGraphGen()
        s = gen.generate(selectors)

        tmp_file = outfile + '.tmp.graph'
        with open(tmp_file, 'w') as f:
            f.write(s.encode('utf8'))

        os.system('dot -T{0} {1} -o {2}'.format(self.__out_type, tmp_file, outfile))


class SelectorGraphGen(GraphGen):
    def __init__(self):
        super(SelectorGraphGen, self).__init__()

    def __gen_selector(self, selector):
        label = u'<TABLE>'
        tags = ' '.join(selector.get_tags())
        label += u'<TR><TD BGCOLOR="darkseagreen1">{0}</TD></TR>'.format(tags)

        label += selector.format('dot-html')

        label += u'</TABLE>'

        s = u'\t"{0}" [label=< {1} >, style="filled", fillcolor="white"];\r\n'.format(
            self.get_obj_id(selector.get_uniq()),
            label)
        return s

    # def __link_entries(self, link):
    #     s = u'\t{0}->{1}->{2} [style="filled"];\r\n'.format(
    #         self.get_obj_id(link.get_master()),
    #         self.get_obj_id(link),
    #         self.get_obj_id(link.get_slave()))
    #     return s

    def generate(self, selectors):
        s = u'digraph D {\r\n'

        for hub in selectors:
            for selector in hub:
                if self.obj_exists(selector.get_uniq()):
                    continue
                self.add_obj(selector.get_uniq())
                s += self.__gen_selector(selector)

        s += u'}\r\n'

        return s
