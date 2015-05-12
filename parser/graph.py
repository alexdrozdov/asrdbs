#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import json


class SentGraph(object):
    def __init__(self, img_type='png'):
        self.__out_type = img_type

    def generate(self, entries, outfile):
        gen = SentGraphGen()
        s = gen.generate(entries)

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

    def __gen_link_label(self, l):
        s = u'\t{0} [label = "{1}", shape="octagon", style="filled", fillcolor="orchid"];\r\n'.format(self.__get_obj_id(l), self.__dict_to_istr(l.explain_str()))
        return s

    def __gen_links(self, form):
        s = u''
        for sl in form.get_slaves():
            s += u'\t{0}->{1}->{2};\r\n'.format(self.__get_obj_id(form), self.__get_obj_id(sl[1]), self.__get_obj_id(sl[0]))
        return s

    def __gen_subgraph(self, e):
        s = u'subgraph cluster_{0} {{\r\n'.format(self.__get_obj_id(e))
        s += u'\tnode [shape="box", style="filled", fillcolor="yellow", fontcolor="black"];\r\n'
        s += u'\tlabel = "{0}";\r\n'.format(e.get_word())
        for f in e.get_forms():
            s += u'\t"{0}" [label="{1}"];\r\n'.format(self.__get_obj_id(f), f.format_info(crlf=True))
        s += u'}\r\n'
        return s

    def generate(self, entries):
        for e in entries:
            self.__add_obj(e)
            for f in e.get_forms():
                self.__add_obj(f)
                for l in f.get_slaves():
                    self.__add_obj(l[1])

        s = u'digraph D {\r\n'
        for e in entries:
            s += self.__gen_subgraph(e)

        for e in entries:
            for f in e.get_forms():
                s += self.__gen_links(f)

        for e in entries:
            for f in e.get_forms():
                for l in f.get_slaves():
                    s += self.__gen_link_label(l[1])

        s += u'}\r\n'

        return s
