#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import copy
import traceback
import functools
import worddb.worddb
from argparse import Namespace as ns
from common.singleton import singleton


class Restricted(object):
    def __cmp__(self, other):
        return 0

    def __eq__(self, other):
        return True

    def __str__(self):
        return "-restricted"

    def __repr__(self):
        return "-restricted"


class Missing(object):
    def __cmp__(self, other):
        return 0

    def __eq__(self, other):
        return True

    def __str__(self):
        return "-missing"

    def __repr__(self):
        return "-missing"


class Formatter(object):
    def __init__(self, cb, fmt):
        self.__cb = cb
        self.__fmt = fmt

    def __call__(self, term):
        return self.__cb(self.__fmt, term)


class _PredefinedFormats(object):
    def __init__(self):
        self.__formatters = {}
        self.__register(
            'dot-html-rows',
            self.__format_html,
            {
                'layer-filter': lambda l: l not in ['private'],
                'tag-filter': lambda t: True,
                'property-filter': lambda p: p not in ['__forms'],
                'aggregate-layer-tags': True,
                'layer-order': ['ro', 'w_once', 'morf', 'ctx', 'sentence'],
                'style': {
                    'align': 'LEFT',
                    'font-color': 'black',
                    'bg-color': 'white',
                    'layers': {
                        'ro': {
                            'align': 'LEFT',
                            'font-color': 'black',
                            'bg-color': 'palegoldenrod',
                        },
                        'w_once': {
                            'bg-color': 'papayawhip',
                        },
                        'morf': {
                            'bg-color': 'peachpuff',
                        },
                        'ctx': {
                            'bg-color': 'lavenderblush',
                        },
                        'sentence': {
                            'bg-color': 'white',
                        },
                    },
                    'tags': {
                    },
                    'properties': {
                        'word': {
                            'font-color': 'black',
                            # 'bg-color': 'white',
                        }
                    },
                },
                '__fmt': {
                    'layer-row-template': '<TR><TD {align} {color} {bgcolor}>{rowdata}</TD><TD {align} {color} {bgcolor}></TD></TR>',
                    'row-template': '<TR><TD {align} {color} {bgcolor}></TD><TD {align} {color} {bgcolor}>{rowdata}</TD></TR>',
                    'color-template': 'COLOR="{color}"',
                    'bg-color-template': 'BGCOLOR="{bgcolor}"',
                    'align-template': 'ALIGN="{align}"',
                }
            }
        )

        self.__register(
            'dict-form',
            self.__format_dict_form,
            {
                'layer-filter': lambda l: l == 'ro',
                'tag-filter': lambda t: True,
                'property-filter': lambda p: True,
                'aggregate-layer-tags': False,
                'deep': False,
                'merge-layers': True,
                'style': {
                },
                '__fmt': {
                }
            }
        )

        self.__register('dot-html-table', self.__format_dot_html_table, {})
        self.__register('dict', self.__format_dict, {})

    def __register(self, name, formatter, fmt):
        self.__formatters[name] = Formatter(formatter, fmt)

    def __prepare_data(self, fmt, term):
        layer_order = fmt['layer-order'] if 'layer-order' in fmt else list(term.layers().keys())
        layers = [ll for ll in layer_order if ll in [l for l in term.layers() if fmt['layer-filter'](l)]]
        tags = dict(
            [(
                        layer,
                        list(filter(
                            lambda t: fmt['tag-filter'](t),
                            term.layer(layer).tags(),
                        ))
                    ) for layer in layers]
        )
        properties = dict(
            [(
                        layer,
                        dict(
                            list(filter(
                                lambda k_v: fmt['property-filter'](k_v[0]),
                                list(term.layer(layer).properties().items()),
                            ))
                        )
                    ) for layer in layers]
        )
        return layers, tags, properties

    def __format_html(self, fmt, term):
        layers, tags, properties = self.__prepare_data(fmt, term)
        res = ''
        style = []
        self.__push_style_stack(style, self.__fmt(fmt, 'style'))
        for l in layers:
            lprops = properties[l]
            ltags = tags[l]
            lstyle = self.__fmt(fmt, 'style', 'layers', l)
            self.__push_style_stack(style, lstyle)
            res += self.__fmt_layer_row(fmt, style, l)
            for t in ltags:
                tstyle = self.__fmt(fmt, 'style', 'tags', t)
                self.__push_style_stack(style, tstyle)
                res += self.__fmt_tag_row(fmt, style, t)
                self.__pop_style_stack(style)
            for p, v in list(lprops.items()):
                pstyle = self.__fmt(fmt, 'style', 'properties', p)
                self.__push_style_stack(style, pstyle)
                res += self.__fmt_prop_row(fmt, style, p, v)
                self.__pop_style_stack(style)
            self.__pop_style_stack(style)
        return res

    def __fmt(self, fmt, *args):
        assert isinstance(fmt, dict) and args
        for a in args:
            if a not in fmt:
                return {}
            fmt = fmt[a]
        return fmt

    def __push_style_stack(self, style, nstyle):
        style.append(
            dict(
                [k_v1 for k_v1 in list(nstyle.items()) if k_v1[0] in ['align', 'font-color', 'bg-color']]
            )
        )

    def __pop_style_stack(self, style):
        style.pop()

    def __fmt_layer_row(self, fmt, style, t):
        align = self.__style_get(style, 'align')
        align = str(self.__fmt(fmt, '__fmt', 'align-template').format(align=align)) if align is not None else ''
        color = self.__style_get(style, 'font-color')
        color = str(self.__fmt(fmt, '__fmt', 'color-template').format(color=color)) if color is not None else ''
        bgcolor = self.__style_get(style, 'bg-color')
        bgcolor = str(self.__fmt(fmt, '__fmt', 'bg-color-template').format(bgcolor=bgcolor)) if bgcolor is not None else ''
        rowdata = str(t)
        return self.__fmt(fmt, '__fmt', 'layer-row-template').format(align=align, color=color, bgcolor=bgcolor, rowdata=rowdata)

    def __fmt_tag_row(self, fmt, style, t):
        align = self.__style_get(style, 'align')
        align = str(self.__fmt(fmt, '__fmt', 'align-template').format(align=align)) if align is not None else ''
        color = self.__style_get(style, 'font-color')
        color = str(self.__fmt(fmt, '__fmt', 'color-template').format(color=color)) if color is not None else ''
        bgcolor = self.__style_get(style, 'bg-color')
        bgcolor = str(self.__fmt(fmt, '__fmt', 'bg-color-template').format(bgcolor=bgcolor)) if bgcolor is not None else ''
        rowdata = str(t)
        return self.__fmt(fmt, '__fmt', 'row-template').format(align=align, color=color, bgcolor=bgcolor, rowdata=rowdata)

    def __fmt_prop_row(self, fmt, style, p, v):
        align = self.__style_get(style, 'align')
        align = str(self.__fmt(fmt, '__fmt', 'align-template').format(align=align)) if align is not None else ''
        color = self.__style_get(style, 'font-color')
        color = str(self.__fmt(fmt, '__fmt', 'color-template').format(color=color)) if color is not None else ''
        bgcolor = self.__style_get(style, 'bg-color')
        bgcolor = str(self.__fmt(fmt, '__fmt', 'bg-color-template').format(bgcolor=bgcolor)) if bgcolor is not None else ''
        rowdata = str('{0}: {1}'.format(str(p), str(v)))
        return self.__fmt(fmt, '__fmt', 'row-template').format(align=align, color=color, bgcolor=bgcolor, rowdata=rowdata)

    def __style_get(self, style, key):
        for l in reversed(style):
            if key in l:
                return l[key]
        return None

    def __format_dict_form(self, fmt, term):
        layers, tags, properties = self.__prepare_data(fmt, term)
        res = {}
        for l in layers:
            lprops = properties[l]
            for p, v in list(lprops.items()):
                res[p] = v
        return res

    def __format_dot_html_table(self, fmt, term):
        s = '<TABLE CELLSPACING="0">'
        s += self['dot-html-rows'](term)
        s += '</TABLE>'
        return s

    def __format_dict(self, fmt, term):
        return copy.deepcopy(term.layers())

    def __getitem__(self, format):
        return self.__formatters[format]


@singleton
class PredefinedFormats(_PredefinedFormats):
    pass


class TermLayer(object):
    def __init__(self, ldict):
        self.__ldict = ldict

    def properties(self):
        return {k: v for k, v in list(self.__ldict.items()) if not k.startswith('#')}

    def tags(self):
        return [k for k in list(self.__ldict.keys()) if k.startswith('#')]


class Term(object):
    layer_order = ['ro', 'w_once', 'morf', 'ctx', 'sentence', 'private']

    def __init__(self, info=None, dct=None, layer_limit=None, reuse_layers=None):
        assert (dct is None and info is not None) or \
            (dct is not None and info is None)
        assert dct is not None or isinstance(info, (dict, Term))
        if dct is not None:
            self.__init_from_dict(dct)
        elif isinstance(info, dict):
            self.__init_from_info(info)
        else:
            self.__init_from_term(
                info,
                layer_limit,
                reuse_layers if reuse_layers is not None else set({})
            )

    def __init_from_term(self, term, layer_limit, reuse_layers,
                         preserve_existant=False, ignore=None):
        assert reuse_layers is None or isinstance(reuse_layers, set)
        assert ignore is None or isinstance(ignore, (list, set, dict))
        if ignore is None:
            ignore = set({'private'})
        mk_empty = False
        if not preserve_existant:
            self.__layers = {}
        for l in Term.layer_order:
            if not mk_empty and l not in ignore:
                if l in reuse_layers:
                    self.__layers[l] = term.__layers[l]
                else:
                    self.__layers[l] = copy.deepcopy(term.__layers[l])
                if layer_limit == l:
                    mk_empty = True
            else:
                self.__layers[l] = {}

    def __init_from_info(self, info):
        self.__layers = {
            'ro': info,
            'w_once': {},
            'morf': {},
            'ctx': {
                'revision': str(uuid.uuid1())
            },
            'sentence': {},
            'private': {},
        }

    def __init_from_dict(self, dct):
        self.__layers = dct

    def copy(self, term, layer_limit=None, reuse_layers=None, ignore=None):
        self.__init_from_term(
            term,
            layer_limit,
            reuse_layers if reuse_layers is not None else set({}),
            preserve_existant=True,
            ignore=ignore
        )

    def add_tag(self, tag, layer):
        assert layer in self.__layers and layer != 'ro',\
            '{0} is missing or ro'.format(layer)

        if tag not in self.__layers[layer]:
            self.__layers['ctx']['revision'] = str(uuid.uuid1())

        self.__layers[layer][tag] = True

    def has_tag(self, tag, layer=None):
        if layer is not None:
            return tag in self.__layers[layer]
        for l in reversed(Term.layer_order):
            if tag in self.__layers[l]:
                return True
        return False

    def add_property(self, property, layer, value):
        assert layer in self.__layers and layer != 'ro'
        assert layer != 'w_once' or property not in self.__layers[layer]

        if property in self.__layers[layer] and \
                self.__layers[layer][property] == Restricted():
            return

        if property not in self.__layers[layer] or \
                self.__layers[layer][property] != value:
            self.__layers['ctx']['revision'] = str(uuid.uuid1())

        self.__layers[layer][property] = value

    def get_property(self, property, layer=None,
                     missing_is_none=False, missing_is_missing=False):
        if layer is not None:
            if property in self.__layers[layer]:
                return self.__layers[layer][property]
        else:
            for l in reversed(Term.layer_order):
                if property in self.__layers[l]:
                    return self.__layers[l][property]
        if missing_is_none:
            return None
        if missing_is_missing:
            return Missing()
        raise KeyError('{0}:{1} doesnt exist'.format(layer, property))

    def restrict_property(self, property, layer=None):
        if layer is not None:
            self.__layers[layer][property] = Restricted()
            return
        for l in reversed(Term.layer_order):
            if layer in self.__layers[l]:
                self.__layers[layer][property] = Restricted()
                return
            self.__layers['ctx'][property] = Restricted()

    def layers(self):
        return self.__layers

    def layer(self, name):
        return TermLayer(self.__layers[name])


class TokenBase(object):
    def __init__(self, info, reuse_layers=None):
        if isinstance(info, dict):
            self.__term = Term(info=info)
        else:
            self.__term = Term(info=info.__term, reuse_layers=reuse_layers)

    def term(self):
        return self.__term

    def revision(self):
        return self.term().get_property('revision', 'ctx')


class DictToken(object):
    def __init__(self, dct):
        self.__term = Term(dct=dct)

    def term(self):
        return self.__term

    def revision(self):
        return self.term().get_property('revision', 'ctx')

    def get_property(self, property, layer=None, missing_is_none=False, missing_is_missing=False):
        return self.term().get_property(
            property,
            layer,
            missing_is_none=missing_is_none,
            missing_is_missing=missing_is_missing
        )

    def format(self, format_spec):
        if isinstance(format_spec, str):
            return self.__predefined_format(str(format_spec))
        assert isinstance(format_spec, dict)
        return self.__custom_format(format_spec)

    def __predefined_format(self, name):
        return PredefinedFormats()[name](self.term())


class TermRoMethods(object):
    def __test_pos(self, pos):
        return self.get_pos() == pos

    def is_adjective(self):
        return self.__test_pos('adjective')

    def is_noun(self):
        return self.__test_pos('noun')

    def is_verb(self):
        return self.__test_pos('verb')

    def is_adverb(self):
        return self.__test_pos('adverb')

    def is_pronoun(self):
        return self.__test_pos('pronoun')

    def is_preposition(self):
        return self.__test_pos('preposition')

    def is_syntax(self):
        return self.__test_pos('syntax')

    def is_comma(self):
        return self.get_word() == ','

    def is_dot(self):
        return self.get_word() == '.'

    def is_question(self):
        return self.get_word() == '?'

    def get_pos(self):
        return self.term().get_property('parts_of_speech', 'ro')

    def get_case(self):
        return self.term().get_property('case')

    def get_gender(self):
        return self.term().get_property('gender')

    def get_count(self):
        return self.term().get_property('count')

    def get_time(self):
        return self.term().get_property('time')

    def get_word(self):
        return self.term().get_property('word')


class TermWriteOnceMethods(object):
    def get_position(self):
        position = self.term().get_property('position')
        if isinstance(position, list):
            return position[0]
        return position

    def get_uniq(self):
        return self.term().get_property('uniq')


class TermCtxMethods(object):
    def get_reliability(self):
        return self.term().get_property('reliability')


class Token(TokenBase, TermRoMethods, TermWriteOnceMethods, TermCtxMethods):
    def __init__(self, based_on, reuse_layers=None):
        assert isinstance(based_on, ns) or isinstance(based_on, Token)
        if isinstance(based_on, ns):
            self.__init_from_params(
                based_on.word,
                based_on.original_word,
                based_on.info,
                based_on.pos,
                based_on.uniq
            )
        else:
            self.__init_from_wordform(based_on, reuse_layers=reuse_layers)

    def __init_from_params(self, word, original_word, info, pos, uniq):
        TokenBase.__init__(
            self,
            dict(list(info.items()) + [('word', word), ])
        )
        self.term().add_property('original_word', 'w_once', original_word)
        self.term().add_property('position', 'w_once', pos)
        self.term().add_property('uniq', 'w_once', uniq)
        self.term().add_property('reliability', 'ctx', 1.0)

    def __init_from_wordform(self, token, reuse_layers):
        TokenBase.__init__(self, token, reuse_layers=reuse_layers)

    def copy(self, reuse_layers):
        return Token(self, reuse_layers)

    def add_tag(self, tag, layer=None):
        assert tag is not None
        if layer is None:
            layer = 'private'
        self.term().add_tag(tag, layer)

    def has_tag(self, tag, layer=None):
        return self.term().has_tag(tag, layer)

    def add_property(self, property, layer, value):
        self.term().add_property(property, layer, value)

    def get_property(self, property, layer=None, missing_is_none=False, missing_is_missing=False):
        return self.term().get_property(
            property,
            layer,
            missing_is_none=missing_is_none,
            missing_is_missing=missing_is_missing
        )

    def format(self, format_spec):
        if isinstance(format_spec, str):
            return self.__predefined_format(str(format_spec))
        assert isinstance(format_spec, dict)
        return self.__custom_format(format_spec)

    def __predefined_format(self, name):
        return PredefinedFormats()[name](self.term())

    def __repr__(self):
        return "Token(word='{0}')".format(self.get_word().encode('utf8'))

    def __str__(self):
        return "Token(word='{0}')".format(self.get_word().encode('utf8'))


class TmpToken(object):
    def __init__(self, term):
        self.__base_term = term
        self.__tmp_term = Term({})

    def add_tag(self, tag, layer):
        return self.__tmp_term.add_tag(tag, layer)

    def has_tag(self, tag, layer=None):
        return self.__tmp_term.has_tag(tag, layer) or self.__base_term.has_tag(tag, layer)

    def add_property(self, property, layer, value):
        self.__tmp_term.add_property(property, layer, value)

    def get_property(self, property, layer=None):
        try:
            return self.__tmp_term.get_property(property, layer)
        except KeyError:
            return self.__base_term.get_property(property, layer)

    def restrict_property(self, property, layer=None):
        self.__tmp_term.restrict_property(property, layer)


class WordForms(object):
    def __init__(self, word, forms):
        self.__word = word
        self.__forms = forms

    def get_forms(self):
        return self.__forms

    def get_word(self):
        return self.__word


class SpecStateIniForm(Token):
    def __init__(self, *args, **argv):
        super(SpecStateIniForm, self).__init__(
            ns(
                word='ini',
                original_word='ini',
                info={'parts_of_speech': 'ini'},
                pos=None,
                uniq=0
            )
        )

    def copy(self, reuse_layers=None):
        return SpecStateIniForm(self, reuse_layers=set())


class SpecStateFiniForm(Token):
    def __init__(self, *args, **argv):
        super(SpecStateFiniForm, self).__init__(
            ns(
                word='fini',
                original_word='fini',
                info={'parts_of_speech': 'fini'},
                pos=None,
                uniq=0
            )
        )

    def copy(self, reuse_layers=None):
        return SpecStateFiniForm(self, reuse_layers=set())


class SpecStateVirtForm(Token):
    def __init__(self, form=None):
        if form is None:
            self.__init_default()
        else:
            self.__init_from_form(form)

    def __init_default(self):
        word = 'virt_' + str(uuid.uuid1())
        super(SpecStateVirtForm, self).__init__(
            ns(
                word=word,
                original_word=word,
                info={'parts_of_speech': 'virt'},
                pos=None,
                uniq=0
            )
        )

    def __defaults(self):
        word = 'virt_' + str(uuid.uuid1())
        super(SpecStateVirtForm, self).__init__(
            ns(
                word=word,
                original_word=word,
                info={'parts_of_speech': 'virt'},
                pos=None,
                uniq=0
            )
        )

    def __init_from_form(self, form):
        super(SpecStateVirtForm, self).__init__(form)

    def copy(self, reuse_layers=None):
        return SpecStateVirtForm(self)

    def add_form(self, form):
        if self.__contains_form(form):
            self.__replace_form(form)
        else:
            self.__add_form(form)

    def __contains_form(self, form):
        forms = self.term().get_property(
            '__forms', 'ctx', missing_is_none=True
        )
        if forms is None or not forms:
            return False
        uniq = form.get_uniq()
        for i, f in enumerate(forms):
            if f['w_once']['uniq'] == uniq:
                return True
        return False

    def __replace_form(self, form):
        forms = self.__unroll_history(form)
        self.__edit_history(forms, form)
        self.__merge_history(forms)

    def __unroll_history(self, form=None):
        forms = self.term().get_property(
            '__forms', 'ctx', missing_is_none=True
        )
        if forms is None:
            return []
        return forms

    def __edit_history(self, forms, replace):
        uniq = replace.get_uniq()
        for i, f in enumerate(forms):
            if f['w_once']['uniq'] == uniq:
                # self.__forms_equal(DictToken(f), replace, exit_on_difference=False)
                forms[i] = replace.format('dict')
                return
        raise ValueError('form not found')

    def __merge_history(self, forms):
        self.__defaults()
        for f in forms:
            self.__add_form(DictToken(f))

    def __append_history(self, form):
        forms = self.term().get_property(
            '__forms', 'ctx', missing_is_none=True
        )
        if forms is None:
            self.term().add_property('__forms', 'ctx', [form.format('dict')])
        else:
            forms.append(form.format('dict'))

    def __add_form(self, form):
        if self.get_pos() == 'virt':
            self.term().copy(form.term(), ignore=['uniq', ])
            self.term().add_property(
                'uniq',
                'ctx',
                str(uuid.uuid3(uuid.NAMESPACE_DNS, form.get_property('uniq')))
            )
            self.__append_history(form)
            # assert self.__forms_equal(self, form)
            return

        resolvers = {
            'parts_of_speech': self.__resolve_same,
            'case': self.__resolve_same,
            'count': self.__resolve_countable,
            'gender': self.__resolve_same,
            'position': self.__resolve_range,
            'uniq': self.__resolve_uniq,
            'word': lambda form, k: self.__resolve_cat(form, k, '_')
        }
        for k, v in list(resolvers.items()):
            v(form, k)

        self.__append_history(form)

    def __forms_equal(self, form, other, exit_on_difference=True):
        layers1 = form.term().layers()
        layers2 = other.term().layers()
        keys1 = set(layers1.keys()) - {'private'}
        keys2 = set(layers2.keys()) - {'private'}
        if keys1 != keys2:
            # print 'differs in keys: {0} -> {1}'.format(keys1, keys2)
            return False
        for k, l1 in list(layers1.items()):
            l2 = layers2[k]
            for kk, v1 in list(l1.items()):
                if kk in ['__forms', 'uniq', 'revision']:
                    continue
                try:
                    v2 = l2[kk]
                except:
                    # print 'key {0}/{1}: is lost'.format(k, kk)
                    if exit_on_difference:
                        return False
                    continue
                if v1 is None and v2 is None:
                    continue
                if v1 == v2:
                    continue
                # print 'differs in {0}/{1}: {2} -> {3}'.format(
                #     k, kk,
                #     v1, v2
                # )
                if exit_on_difference:
                    return False
        return True

    # def __resolve_hierarchical(self, form, k):
    #     my_prop = self.term().get_property(k)
    #     other_prop = form.term().get_property(k)
    #     if my_prop == other_prop:
    #         return
    #     common = find_common(my_prop, other_prop)
    #     for a, v in get_attributes(common).items():
    #         self.term().add_property(a, 'ctx', v)

    def __resolve_same(self, form, k):
        my_prop = self.term().get_property(k, missing_is_missing=True)
        other_prop = form.term().get_property(k, missing_is_missing=True)
        if my_prop == Restricted() or other_prop == Restricted():
            self.term().restrict_property(k)
        elif my_prop is None and other_prop is not None:
            self.term().add_property(k, 'ctx', other_prop)
        elif my_prop == Missing() or other_prop == Missing():
            self.term().restrict_property(k)
        elif my_prop == other_prop:
            return
        else:
            self.term().restrict_property(k)

    def __resolve_countable(self, form, k):
        my_prop = self.term().get_property(k)
        other_prop = form.term().get_property(k)
        if my_prop is None and other_prop is not None:
            self.term().add_property(k, 'ctx', other_prop)
        else:
            self.term().add_property(k, 'ctx', 'plural')

    def __resolve_range(self, form, k):
        my_prop = self.term().get_property(k)
        other_prop = form.term().get_property(k)
        if my_prop is None and other_prop is not None:
            self.term().add_property(k, 'ctx', other_prop)
        else:
            my_prop = my_prop if isinstance(my_prop, list) else [my_prop, ]
            other_prop = other_prop if isinstance(other_prop, list) else [other_prop, ]
            self.term().add_property(
                k,
                'ctx',
                sorted(
                    [x for x in list(set(my_prop + other_prop)) if x is not None]
                )
            )

    def __resolve_uniq(self, form, k):
        my_uniq = self.term().get_property(k)
        other_uniq = form.term().get_property(k)
        referers_uuids = '.'.join(
            sorted([my_uniq, other_uniq])
        )
        self.term().add_property(
            'uniq',
            'ctx',
            str(uuid.uuid3(uuid.NAMESPACE_DNS, referers_uuids))
        )

    def __resolve_cat(self, form, k, sep):
        my_prop = self.term().get_property(k)
        other_prop = form.term().get_property(k)
        if my_prop is None and other_prop is not None:
            self.term().add_property(k, 'ctx', other_prop)
        else:
            self.term().add_property(k, 'ctx', my_prop + sep + other_prop)


class SentenceFini(object):
    def __init__(self):
        self.__entries = [SpecStateFiniForm()]

    def get_word(self):
        return 'fini'

    def get_uniq(self):
        return 0

    def get_forms(self):
        return self.__entries


class WordFormFabric(object):
    def __init__(self, worddb_file):
        self.__wdb = worddb.worddb.Worddb(worddb_file)
        self.__form_uniq = str(uuid.uuid1())

    def create(self, word, position):
        if word in '.,;-!?':
            return self.__create_syntax_entry(word, position)
        return self.__create_word_entry(word, position)

    def __unused(self, *args, **kwargs):
        pass

    def __validate_info(self, info):
        try:
            info = eval(info['info'])
            if info['parts_of_speech'] in ['noun', 'pronoun', 'adjective']:
                self.__unused(info['case'])
                self.__unused(info['count'])
            return True
        except:
            print("Info validation failed for", info)
            print(traceback.format_exc())
            return False

    def __create_syntax_entry(self, symbol, position):
        se = Token(
            ns(
                word=symbol,
                original_word=symbol,
                info={'parts_of_speech': 'syntax'},
                pos=position,
                uniq=str(uuid.uuid1())
            )
        )
        wf = WordForms(symbol, [se, ])
        return wf

    def __create_word_entry(self, word, position):
        res = []
        word = word.lower()
        info = self.__wdb.get_word_info(word)
        assert isinstance(info, list), "No info avaible for {0}".format(word)
        for form in [form for form in functools.reduce(
                lambda x, y: x + y,
                [i['form'] for i in info]
            ) if self.__validate_info(form)]:
            res.append(
                Token(
                    ns(
                        word=form['word'],
                        original_word=word,
                        info=eval(form['info']),
                        pos=position,
                        uniq=self.__form_uniq
                    )
                )
            )
            self.__form_uniq = str(uuid.uuid1())
        wf = WordForms(word, res)
        return wf
