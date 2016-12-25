#!/usr/bin/env python
# -*- #coding: utf8 -*-


import os
import re
import json
import uuid
import functools
import parser.spare.atjson
import parser.spare.relations
import common.config
import common.dg
from common.singleton import singleton
from argparse import Namespace as ns


class SelectorRes(object):
    def __init__(self, res, link_attrs=None, info=None):
        self.res = res
        self.link_attrs = {} if link_attrs is None else link_attrs
        self.info = {} if info is None else info

    def __bool__(self):
        return self.res

    def __and__(self, other):
        if self.res and other.res:
            return SelectorRes(
                True,
                dict(list(self.link_attrs.items()) + list(other.link_attrs.items())),
                dict(list(self.info.items()) + list(other.info.items())),
            )
        return SelectorRes(False)

    def __or__(self, other):
        if self.res or other.res:
            return SelectorRes(
                True,
                dict(list(self.link_attrs.items()) + list(other.link_attrs.items())),
                dict(list(self.info.items()) + list(other.info.items())),
            )
        return SelectorRes(False)

    def __add__(self, other):
        return SelectorRes(
            self.res,
            dict(list(self.link_attrs.items()) + list(other.link_attrs.items())),
            dict(list(self.info.items()) + list(other.info.items())),
        )

    def __str__(self):
        return 'SelectorRes({0}, link_attrs={1}, info={2})'.format(
            self.res,
            self.link_attrs,
            self.info
        )

    def __repr__(self):
        return 'SelectorRes({0}, link_attrs={1}, info={2})'.format(
            self.res,
            self.link_attrs,
            self.info
        )


class _TagRelations(object):
    def __init__(self):
        pass

    def add_tag(self, tag, subtags):

        t_ns = ns(
            namespace='selectors',
            name=tag,
            description=''
        )
        r_ns = ns(
            namespace='selectors',
            name='subtype',
            description=''
        )
        parser.spare.relations.Relations().create_term(t_ns)
        parser.spare.relations.Relations().create_term(r_ns)
        for subtag in subtags:
            st_ns = ns(
                namespace='selectors',
                name='subtype',
                description=''
            )
            parser.spare.relations.Relations().create_term(st_ns)
            parser.spare.relations.Relations().add_relation(
                (t_ns, st_ns),
                r_ns
            )


class Selector(common.dg.SingleNode):
    def __init__(self, tags, clarifies, rules):
        assert None not in tags
        assert None not in clarifies
        self.__uniq = uuid.uuid1()
        self.__tags = tags
        self.__clarifies = clarifies
        self.__rules = rules

    def get_tags(self):
        return self.__tags

    def get_autotag(self):
        return self.__tags[-1]

    def get_uniq(self):
        return self.__uniq

    def get_clarifies(self):
        return self.__clarifies

    def get_slaves(self):
        return [Selectors()[tag] for tag in self.__clarifies]

    def apply(self, form):
        return self.__apply(form, test_only=False)

    def test(self, form):
        return self.__apply(form, test_only=True)

    def __apply(self, form, test_only=False):
        for c in self.__clarifies:
            assert c is not None
            if not self.__check_clarify(form, c):
                return self.__failure()
        for r in self.__rules:
            if not r.match(form):
                return self.__failure()
        self.__set_tags(form)
        return SelectorRes(
            True,
            link_attrs={},
            info=self.__list_rules()
        )

    def __list_rules(self):
        return dict(
            functools.reduce(
                lambda x, y: x + y,
                [list(r.format('dict').items()) for r in self.__rules],
                []
            )
        )

    def __failure(self):
        return SelectorRes(False)

    def __check_clarify(self, form, tag):
        if form.has_tag(tag):
            return True
        selector = Selectors()[tag]
        return selector(form)

    def __set_tags(self, form):
        for t in self.__tags:
            form.add_tag(t, 'morf')

    def __call__(self, *argc, **argv):
        test_only = argv['test_only'] if 'test_only' in argv else False
        return self.__apply(argc[0], test_only=test_only)

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        elif fmt == 'dot-html-rows':
            return self.__format_dot_html_rows()
        else:
            raise RuntimeError('Unsupported format {0}'.format(fmt))

    def __format_dict(self):
        return {
            'type': 'selector',
            'tags': list(self.__tags),
            'clarifies': list(self.__clarifies),
            'rules': [r.format('dict') for r in self.__rules]
        }

    def __format_dot_html_rows(self):
        s = '<TR><TD BGCOLOR="darkseagreen1">type:selector</TD></TR>'
        s += '<TR><TD BGCOLOR="darkseagreen1">clarifies: {0}</TD></TR>'.format(
            ' '.join(self.__clarifies)
        )
        s += functools.reduce(
            lambda x, y: x + y,
            [
                '<TR><TD BGCOLOR="darkseagreen1">{0}</TD></TR>'.format(
                    str(r.format('dict'))
                ) for r in self.__rules
            ],
            ''
        )
        return s

    def __repr__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )

    def __str__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )


class MultiSelector(common.dg.SingleNode):
    def __init__(self, tags, clarifies, rules, link_attrs, index):
        self.__uniq = uuid.uuid1()
        self.__tags = tags
        self.__clarifies = clarifies
        self.__rules = rules
        self.__link_attrs = link_attrs
        self.__index = index

    def get_tags(self):
        return [t.name for t in self.__tags]

    def get_autotag(self):
        for t in self.__tags:
            if t.auto:
                return t.name
        return None

    def get_uniq(self):
        return self.__uniq

    def get_clarifies(self):
        return self.__clarifies

    def get_slaves(self):
        return [Selectors()[tag] for tag in self.__clarifies]

    def apply(self, *forms):
        return self.__apply(forms, test_only=False)

    def test(self, *form):
        return self.__apply(form, test_only=True)

    def __failure(self):
        return SelectorRes(False)

    def __apply(self, forms, test_only=False):
        tag_suffix = '/' + '+'.join(sorted([f.get_uniq() for f in forms]))
        res = SelectorRes(True)
        for c in self.__clarifies:
            res = res and self.__check_clarify(forms, c, tag_suffix)
            if not res:
                return self.__failure()

        for r in self.__rules:
            if not r.match(*forms):
                # raise ValueError()
                return self.__failure()

        form = forms[self.__index]
        self.__set_tags(form, tag_suffix)

        return res + SelectorRes(
            False,
            link_attrs=self.__link_attrs,
            info=self.__list_rules()
        )

    def __list_rules(self):
        return dict(
            functools.reduce(
                lambda x, y: x + y,
                [list(r.format('dict').items()) for r in self.__rules],
                []
            )
        )

    def __check_clarify(self, forms, tag, tag_suffix):
        form = forms[self.__index]
        if form.has_tag(tag) or form.has_tag(tag + tag_suffix):
            return SelectorRes(True)
        if form.restricted(tag) or form.restricted(tag + tag_suffix):
            return SelectorRes(False)
        selector = Selectors()[tag]
        # fixed_index is required by SelectorHub with single form Selector
        r = selector.invoke(*forms, fixed_index=self.__index)
        if not r:
            # Here we can be shure this tag is inapplicable
            form.restrict_property(tag + tag_suffix)
        return r

    def __set_tags(self, form, tag_suffix):
        for t in self.__tags:
            tag_name = t.name + tag_suffix if t.auto or t.base else t.name
            form.add_tag(tag_name, 'ctx')

    def __call__(self, *argc, **argv):
        test_only = argv['test_only'] if 'test_only' in argv else False
        return self.__apply(argc, test_only=test_only)

    def format(self, fmt):
        if fmt == 'dict':
            return self.__format_dict()
        elif fmt == 'dot-html-rows':
            return self.__format_dot_html_rows()
        else:
            raise RuntimeError('Unsupported format {0}'.format(fmt))

    def __format_dict(self):
        return {
            'index': self.__index,
            'type': 'multiselector',
            'tags': [vars(t) for t in self.__tags],
            'clarifies': list(self.__clarifies),
            'rules': [r.format('dict') for r in self.__rules]
        }

    def __format_dot_html_rows(self):
        s = '<TR><TD BGCOLOR="darkseagreen1">type: multiselector</TD></TR>'
        s += '<TR><TD BGCOLOR="darkseagreen1">clarifies: {0}</TD></TR>'.format(
            ' '.join(self.__clarifies)
        )
        s += functools.reduce(
            lambda x, y: x + y,
            [
                '<TR><TD BGCOLOR="darkseagreen1">{0}</TD></TR>'.format(
                    str(r.format('dict'))
                ) for r in self.__rules
            ],
            ''
        )
        return s

    def __repr__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )

    def __str__(self):
        return "Selector(tags={0}, clarifies={1})".format(
            self.get_tags(),
            self.__clarifies
        )


class SelectorHub(common.dg.MultiNode):
    def __init__(self, tag):
        self.__tag = tag
        self.__selectors = []
        self.__is_single = None

    def get_tag(self):
        return self.__tag

    def add_selector(self, selector):
        is_single = isinstance(selector, Selector)
        assert self.__is_single is None or self.__is_single == is_single
        self.__is_single = is_single
        self.__selectors.append(selector)

    def __apply(self, *argc, **argv):
        return functools.reduce(
            lambda x, y: x or y,
            [s(*argc, **argv) for s in self.__selectors],
            SelectorRes(False)
        )

    def __is_single_selector(self):
        return self.__is_single

    def get_selectors(self):
        return self.__selectors

    def get_objects(self):
        return self.__selectors

    def apply(self, *argc, **argv):
        return self.__apply(*argc, test_only=False)

    def test(self, *argc, **argv):
        return self.__apply(*argc, test_only=True)

    def invoke(self, *args, **argv):
        test_only = argv['test_only'] if 'test_only' in argv else False
        fixed_index = argv['fixed_index'] if 'fixed_index' in argv else None
        if self.__is_single_selector():
            return self.__apply(args[fixed_index], test_only=test_only)
        return self.__apply(*args, test_only=test_only)

    def format(self, fmt):
        if fmt == 'dict':
            return self.__to_dict()
        raise RuntimeError('Unsupported format {0}'.format(fmt))

    def __to_dict(self):
        return {
            'type':
                'single' if self.__is_single else
                'none' if self.__is_single is None else
                'multy',
            'tag': self.__tag,
            'name': self.__tag,
        }

    def __call__(self, *argc, **argv):
        return self.__apply(*argc, **argv)

    def __repr__(self):
        return "SelectorHub({0})".format(self.get_tag())

    def __str__(self):
        return "SelectorHub({0})".format(self.get_tag())

    def __iter__(self):
        for s in self.__selectors:
            yield s


class _Preprocessor(parser.spare.atjson.AtJson):
    def __init__(self):
        super().__init__(namespace='selectors')


class _Compiler(object):
    def __init__(self):
        pass

    def compile(self, js, clarifies=None, base_tags=None):
        js = Preprocessor().preprocess(js)
        if clarifies is None:
            clarifies = []
        if 'selector' in js:
            return self.__compile(js['selector'], clarifies, base_tags)
        if 'multi' in js:
            return self.__multi(js['multi'])
        raise KeyError('neither selector nor multi key found in selector spec')

    def __multi(self, js):
        terms_count = self.__eval_terms_count(js)
        tag_base = [ns(
            name=t,
            auto=False,
            base=True
        ) for t in self.__get_property_list(js, 'tag-base')]
        js = self.__reshape_js_base(js, terms_count)
        index = self.__find_internal_layer(js, terms_count)
        if index is not None:
            index = list(js.keys())[0]
            js = js[index]
            index = int(index)
            return self.__compile_layer(terms_count, index, js, base_tags=tag_base)
        return []

    def __compile_layer(self, terms_count, index, js, parent_tag=None, base_tags=None):
        base_tags = [ns(
            name=t,
            auto=False,
            base=True
        ) for t in self.__get_property_list(js, 'tag-base')] + \
            self.__as_list(base_tags, none_is_empty=True)

        tags = [ns(
            name=t,
            auto=False,
            base=False
        ) for t in self.__get_property_list(js, 'tag')]

        clarifies = self.__get_property_list(js, 'clarifies') + \
            self.__as_list(parent_tag, none_is_empty=True)

        if 'link' in js:
            link_attrs = js['link']
        else:
            link_attrs = {}

        rules = functools.reduce(
            lambda x, y: x + y,
            [self.__mk_multi_rule(index, r_v[0], r_v[1]) for r_v in self.__rules(js)],
            []
        )

        auto_tag = ns(
            name='#' + str(uuid.uuid1()),
            auto=True,
            base=False
        )

        selector_tags = tags + [auto_tag, ]
        if link_attrs or tags:
            selector_tags += base_tags

        ss = []
        sss = []
        i_index = self.__find_internal_layer(js, terms_count)
        if i_index is not None:
            i_js = js[str(i_index)]
            rrr = self.__compile_layer(
                terms_count,
                i_index,
                i_js,
                None,   # auto_tag.name,
                base_tags
            )

            ss.extend(rrr)
            sss.append(rrr[0])

        s = [MultiSelector(
            selector_tags,
            clarifies + [ssss.get_autotag() for ssss in sss],
            rules,
            link_attrs,
            index=index
        ), ]

        s.extend(ss)

        clarify = self.__get_property_list(js, 'clarify')
        for c_js in clarify:
            s.extend(
                self.__compile_layer(
                    terms_count,
                    index,
                    c_js,
                    auto_tag.name,
                    base_tags
                )
            )

        return s

    def __find_internal_layer(self, js, terms_count):
        for i in range(terms_count):
            if str(i) in js:
                return i
        return None

    def __eval_terms_count(self, js):
        n = 0
        while str(n) in js:
            n += 1
        return n

    def __find_deepest_term(self, js, max_count):
        test_set = set(['clarify', ] + [str(x) for x in range(max_count)])
        for i in range(max_count):
            t = js[str(i)]
            if test_set.intersection(t):
                return i
        raise ValueError(
            'no one item with clarifies found in {0}'.format(js)
        )

    def __move_js_base_clarifies(self, js, res):
        if 'clarifies' not in js:
            return

        d = list(res.values())[0]
        if 'clarifies' not in d:
            d['clarifies'] = []
        elif isinstance(d['clarifies'], str):
            d['clarifies'] = [d['clarifies'], ]
        if js['clarifies'] not in d['clarifies']:
            d['clarifies'].append(js['clarifies'])

    def __reshape_js_base(self, js, terms_count):
        if terms_count is None:
            terms_count = self.__eval_terms_count(js)
        deepest = self.__find_deepest_term(js, terms_count)
        res = {
            str(deepest): js[str(deepest)]
        }
        self.__move_js_base_clarifies(js, res)
        for i in range(terms_count):
            if i == deepest:
                continue
            res = {
                str(i): dict(list(js[str(i)].items()) + list(res.items()))
            }
        return res

    def __compile(self, js, clarifies, base_tags):
        assert base_tags is None or None not in base_tags
        selectors = []

        tags = self.__get_property_list(js, 'tag')
        assert None not in tags
        base_tags = self.__as_list(base_tags, none_is_empty=True) +\
            self.__get_property_list(js, 'tag-base')
        assert None not in base_tags
        clarifies = self.__as_list(clarifies)

        clarifies.extend(self.__get_property_list(js, 'clarifies'))
        rules = functools.reduce(
            lambda x, y: x + y,
            [self.__mk_single_rule(r_v1[0], r_v1[1]) for r_v1 in self.__rules(js)],
            []
        )

        if tags:
            selectors.append(Selector(tags + base_tags, clarifies, rules))

        for c in self.__get_property_list(js, 'clarify'):
            selectors.extend(self.__compile(c, tags, base_tags))

        return selectors

    def __tags(self, selectors):
        return sorted(list(set(
            functools.reduce(
                lambda x, y: x + y,
                [s.get_tags() for s in selectors],
                []
            )
        )))

    def __get_property_list(self, js, name, default=None):
        v = [] if default is None else self.__as_list(default)
        if name in js:
            v = self.__as_list(js[name])
        return v

    def __as_list(self, v, none_is_empty=False):
        if none_is_empty and v is None:
            return []
        if not isinstance(v, list):
            v = [v, ]
        return list(v)

    def __rules(self, js):
        known_rules = [
            'pos', 'case', 'animation',
            'position', 'equal-properties',
            'word', 'bind-props', 'enable-props',
        ]
        return [(k, js[k]) for k in [k for k in list(js.keys()) if k in known_rules]]

    def __mk_single_rule(self, k, v):
        if not isinstance(v, list):
            return [v.create_single(), ]
        return [vv.create_single() for vv in v]

    def __mk_multi_rule(self, index, k, v):
        if not isinstance(v, list):
            return [v.create_multi(index), ]
        return [vv.create_multi(index) for vv in v]


class _Selectors(object):
    def __init__(self):
        self.__selectors = {}
        self.__load_selectors()

    def __load_selectors(self):
        cfg = common.config.Config()
        if not cfg.exists('/parser/selectors'):
            return
        for d in cfg['/parser/selectors']:
            for f in [fname for fname in os.listdir(d) if fname.endswith('.json')]:
                path = os.path.join(d, f)
                if path.endswith('.multi.json'):
                    self.__load_multi(path)
                else:
                    self.__load_single(path)

    def __load_single(self, path):
        with open(path) as fp:
            res = Compiler().compile(json.load(fp))
            self.__add_selectors(res)

    def __load_multi(self, path):
        with open(path) as fp:
            data = fp.read()
            for s in [_f for _f in re.split('^//.*\n', data, flags=re.MULTILINE) if _f]:
                res = Compiler().compile(json.loads(s))
                self.__add_selectors(res)

    def __add_selectors(self, r):
        for s in r:
            for t in s.get_tags():
                if t in self.__selectors:
                    sh = self.__selectors[t]
                else:
                    sh = SelectorHub(t)
                    self.__selectors[t] = sh
                sh.add_selector(s)

    def __getitem__(self, index):
        return self.__selectors[index]

    def __iter__(self):
        for v in list(self.__selectors.values()):
            yield v


@singleton
class Preprocessor(_Preprocessor):
    pass


@singleton
class Compiler(_Compiler):
    pass


@singleton
class Selectors(_Selectors):
    pass


@singleton
class TagRelations(_TagRelations):
    pass


def selector(name):
    return Selectors()[name]
