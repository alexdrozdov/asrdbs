#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import copy
import traceback
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
            'dot-html',
            self.__format_html,
            {
                'layer-filter': lambda l: True,
                'tag-filter': lambda t: True,
                'property-filter': lambda p: True,
                'aggregate-layer-tags': True,
                'style': {
                    'align': 'LEFT',
                    'font-color': 'black',
                    'bg-color': 'white',
                    'layers': {
                        'ro': {
                            'align': 'LEFT',
                            'font-color': 'black',
                            'bg-color': 'white',
                        },
                    },
                    'tags': {
                    },
                    'properties': {
                        'word': {
                            'font-color': 'black',
                            'bg-color': 'white',
                        }
                    },
                },
                '__fmt': {
                    'row-template': u'<TR><TD {align} {color} {bgcolor}>{rowdata}</TD></TR>',
                    'color-template': u'COLOR="{color}"',
                    'bg-color-template': u'BGCOLOR="{bgcolor}"',
                    'align-template': 'ALIGN="{align}"',
                }
            }
        )

        self.__register(
            'dict-form',
            self.__format_dict,
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

    def __register(self, name, formatter, fmt):
        self.__formatters[name] = Formatter(formatter, fmt)

    def __prepare_data(self, fmt, term):
        layers = filter(
            lambda l: fmt['layer-filter'](l),
            term.layers()
        )
        tags = dict(
            map(
                lambda layer:
                    (
                        layer,
                        filter(
                            lambda t: fmt['tag-filter'](t),
                            term.layer(layer).tags(),
                        )
                    ),
                layers
            )
        )
        properties = dict(
            map(
                lambda layer:
                    (
                        layer,
                        dict(
                            filter(
                                lambda (k, v): fmt['property-filter'](k),
                                term.layer(layer).properties().items(),
                            )
                        )
                    ),
                layers
            )
        )
        return layers, tags, properties

    def __format_html(self, fmt, term):
        layers, tags, properties = self.__prepare_data(fmt, term)
        res = u''
        style = []
        self.__push_style_stack(style, self.__fmt(fmt, 'style'))
        for l in layers:
            lprops = properties[l]
            ltags = tags[l]
            lstyle = self.__fmt(fmt, 'style', 'layers', l)
            self.__push_style_stack(style, lstyle)
            for t in ltags:
                tstyle = self.__fmt(fmt, 'style', 'tags', t)
                self.__push_style_stack(style, tstyle)
                res += self.__fmt_tag_row(fmt, style, t)
                self.__pop_style_stack(style)
            for p, v in lprops.items():
                pstyle = self.__fmt(fmt, 'style', 'properties', p)
                self.__push_style_stack(style, pstyle)
                res += self.__fmt_prop_row(fmt, style, p, v)
                self.__pop_style_stack(style)
            self.__pop_style_stack(style)
        return res

    def __fmt(self, fmt, *args):
        assert isinstance(fmt, dict) and args
        for a in args:
            if not fmt.has_key(a):
                return {}
            fmt = fmt[a]
        return fmt

    def __push_style_stack(self, style, nstyle):
        style.append(
            dict(
                filter(
                    lambda (k, v): k in ['align', 'font-color', 'bg-color'],
                    nstyle.items()
                )
            )
        )

    def __pop_style_stack(self, style):
        style.pop()

    def __fmt_tag_row(self, fmt, style, t):
        align = self.__style_get(style, 'align')
        align = unicode(self.__fmt(fmt, '__fmt', 'align-template').format(align=align)) if align is not None else u''
        color = self.__style_get(style, 'font-color')
        color = unicode(self.__fmt(fmt, '__fmt', 'color-template').format(color=color)) if color is not None else u''
        bgcolor = self.__style_get(style, 'bg-color')
        bgcolor = unicode(self.__fmt(fmt, '__fmt', 'bg-color-template').format(bgcolor=bgcolor)) if bgcolor is not None else u''
        rowdata = unicode(t)
        return self.__fmt(fmt, '__fmt', 'row-template').format(align=align, color=color, bgcolor=bgcolor, rowdata=rowdata)

    def __fmt_prop_row(self, fmt, style, p, v):
        align = self.__style_get(style, 'align')
        align = unicode(self.__fmt(fmt, '__fmt', 'align-template').format(align=align)) if align is not None else u''
        color = self.__style_get(style, 'font-color')
        color = unicode(self.__fmt(fmt, '__fmt', 'color-template').format(color=color)) if color is not None else u''
        bgcolor = self.__style_get(style, 'bg-color')
        bgcolor = unicode(self.__fmt(fmt, '__fmt', 'bg-color-template').format(bgcolor=bgcolor)) if bgcolor is not None else u''
        rowdata = unicode(u'{0}: {1}'.format(unicode(p), unicode(v)))
        return self.__fmt(fmt, '__fmt', 'row-template').format(align=align, color=color, bgcolor=bgcolor, rowdata=rowdata)

    def __style_get(self, style, key):
        for l in reversed(style):
            if l.has_key(key):
                return l[key]
        return None

    def __format_dict(self, fmt, term):
        layers, tags, properties = self.__prepare_data(fmt, term)
        res = {}
        for l in layers:
            lprops = properties[l]
            for p, v in lprops.items():
                res[p] = v
        return res

    def __getitem__(self, format):
        return self.__formatters[format]


@singleton
class PredefinedFormats(_PredefinedFormats):
    pass


class TermLayer(object):
    def __init__(self, ldict):
        self.__ldict = ldict

    def properties(self):
        return {k: v for k, v in self.__ldict.items() if not k.startswith('#')}

    def tags(self):
        return [k for k in self.__ldict.keys() if k.startswith('#')]


class Term(object):
    layer_order = ['ro', 'w_once', 'morf', 'ctx', 'sentence', 'private']

    def __init__(self, info, layer_limit=None, reuse_layers=None):
        assert isinstance(info, (dict, Term))
        if isinstance(info, dict):
            self.__init_from_info(info)
        else:
            self.__init_from_term(
                info,
                layer_limit,
                reuse_layers if reuse_layers is not None else set({})
            )

    def __init_from_term(self, term, layer_limit, reuse_layers, preserve_existant=False, ignore=None):
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
            'ctx': {},
            'sentence': {},
            'private': {},
        }

    def copy(self, term, layer_limit=None, reuse_layers=None, ignore=None):
        self.__init_from_term(
            term,
            layer_limit,
            reuse_layers if reuse_layers is not None else set({}),
            preserve_existant=True,
            ignore=ignore
        )

    def add_tag(self, tag, layer):
        assert self.__layers.has_key(layer) and layer != 'ro',\
            '{0} is missing or ro'.format(layer)

        self.__layers[layer][tag] = True

    def has_tag(self, tag, layer=None):
        if layer is not None:
            return self.__layers[layer].has_key(tag)
        for l in reversed(Term.layer_order):
            if self.__layers[l].has_key(tag):
                return True
        return False

    def add_property(self, property, layer, value):
        assert self.__layers.has_key(layer) and layer != 'ro'
        assert layer != 'w_once' or not self.__layers[layer].has_key(property)
        if self.__layers[layer].has_key(property) and self.__layers[layer][property] == Restricted():
            return
        self.__layers[layer][property] = value

    def get_property(self, property, layer=None):
        if layer is not None:
            return self.__layers[layer][property]
        for l in reversed(Term.layer_order):
            if self.__layers[l].has_key(property):
                return self.__layers[l][property]
        raise KeyError('{0}:{1} doesnt exist'.format(layer, property))

    def restrict_property(self, property, layer=None):
        if layer is not None:
            self.__layers[layer][property] = Restricted()
            return
        for l in reversed(Term.layer_order):
            if self.__layers[l].has_key(layer):
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
            self.__term = Term(info)
        else:
            self.__term = Term(info.__term, reuse_layers=reuse_layers)

    def term(self):
        return self.__term


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
        return self.get_word() == u','

    def is_dot(self):
        return self.get_word() == u'.'

    def is_question(self):
        return self.get_word() == u'?'

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

    def get_property(self, property, layer=None):
        return self.term().get_property(property, layer)

    def format(self, format_spec):
        if isinstance(format_spec, (str, unicode)):
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
                word=u'ini',
                original_word=u'ini',
                info={'parts_of_speech': u'ini'},
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
                word=u'fini',
                original_word=u'fini',
                info={'parts_of_speech': u'fini'},
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
        word = u'virt_' + unicode(uuid.uuid1())
        super(SpecStateVirtForm, self).__init__(
            ns(
                word=word,
                original_word=word,
                info={'parts_of_speech': u'virt'},
                pos=None,
                uniq=0
            )
        )

    def __init_from_form(self, form):
        super(SpecStateVirtForm, self).__init__(form)

    def copy(self, reuse_layers=None):
        return SpecStateVirtForm(self)

    def add_form(self, form):
        if self.get_pos() == u'virt':
            self.term().copy(form.term(), ignore=['uniq', ])
            self.term().add_property(
                'uniq',
                'ctx',
                str(uuid.uuid3(uuid.NAMESPACE_DNS, form.get_property('uniq')))
            )
            return

        resolvers = {
            'parts_of_speech': self.__resolve_same,
            'case': self.__resolve_same,
            'count': self.__resolve_countable,
            'gender': self.__resolve_same,
            'position': self.__resolve_range,
            'uniq': self.__resolve_uniq,
            'word': lambda form, k: self.__resolve_cat(form, k, u'_')
        }
        for k, v in resolvers.items():
            v(form, k)

    # def __resolve_hierarchical(self, form, k):
    #     my_prop = self.term().get_property(k)
    #     other_prop = form.term().get_property(k)
    #     if my_prop == other_prop:
    #         return
    #     common = find_common(my_prop, other_prop)
    #     for a, v in get_attributes(common).items():
    #         self.term().add_property(a, 'ctx', v)

    def __resolve_same(self, form, k):
        my_prop = self.term().get_property(k)
        other_prop = form.term().get_property(k)
        if my_prop is None and other_prop is not None:
            self.term().add_property(k, 'ctx', other_prop)
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
                    filter(lambda x: x is not None, list(set(my_prop + other_prop)))
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
        return u'fini'

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
            print "Info validation failed for", info
            print traceback.format_exc()
            return False

    def __create_syntax_entry(self, symbol, position):
        se = Token(
            ns(
                word=symbol,
                original_word=symbol,
                info={'parts_of_speech': u'syntax'},
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
        assert isinstance(info, list), u"No info avaible for {0}".format(word)
        for form in filter(
            lambda form: self.__validate_info(form),
            reduce(
                lambda x, y: x + y,
                map(
                    lambda i: i['form'],
                    info
                )
            )
        ):
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
