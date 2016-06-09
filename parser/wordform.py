#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import copy
import traceback
import worddb.worddb
from argparse import Namespace as ns
from common.singleton import singleton


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

    def __init__(self, info, layer_limit='morf', copy_layers=None):
        assert isinstance(info, (dict, Term))
        if isinstance(info, dict):
            self.__init_from_info(info)
        else:
            self.__init_from_term(
                info,
                layer_limit,
                copy_layers if copy_layers is not None else set({})
            )

    def __init_from_term(self, term, layer_limit, copy_layers):
        assert copy_layers is None or isinstance(copy_layers, set)
        mk_empty = False
        self.__layers = {}
        for l in Term.layer_order:
            if not mk_empty:
                if l in copy_layers:
                    self.__layers[l] = copy.deepcopy(term.__layers[l])
                else:
                    self.__layers[l] = term.__layers[l]
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
        self.__layers[layer][property] = value

    def get_property(self, property, layer=None):
        if layer is not None:
            return self.__layers[layer][property]
        for l in reversed(Term.layer_order):
            if self.__layers[l].has_key(property):
                return self.__layers[l][property]
        raise KeyError('{0}:{1} doesnt exist'.format(layer, property))

    def layers(self):
        return self.__layers

    def layer(self, name):
        return TermLayer(self.__layers[name])


class SentenceEntry(object):

    word = 1
    syntax = 2

    def __init__(self, original_word, is_word=False, is_syntax=False):
        assert original_word is not None
        self.__original = original_word
        if not is_word and not is_syntax:
            raise ValueError("Undefined entry type")
        if is_word and is_syntax:
            raise ValueError("Undefined entry type")
        if is_word:
            self.__type = SentenceEntry.word
            return
        if is_syntax:
            self.__type = SentenceEntry.syntax
            return

    def is_word(self):
        return self.__type == SentenceEntry.word

    def is_syntax(self):
        return self.__type == SentenceEntry.syntax

    def get_original(self):
        return self.__original


class SyntaxEntry(SentenceEntry):
    def __init__(self, symbol, original_symbol, position, uniq):
        SentenceEntry.__init__(self, original_word=original_symbol, is_syntax=True)
        self.__symbol = symbol
        self.__pos = position
        self.__uniq = uniq

    def is_comma(self):
        return self.__symbol == ','

    def is_dot(self):
        return self.__symbol == '.'

    def is_question(self):
        return self.__symbol == '?'

    def get_pos(self):
        return 'syntax'

    def get_word(self):
        return self.__symbol

    def get_position(self):
        return self.__pos

    def get_uniq(self):
        return self.__uniq

    def __format_info(self, sep=None, head='', tail=''):
        short_names = {
            'parts_of_speech': 'pos',
            'case': 'case',
            'gender': 'gender',
            'count': 'count',
            'time': 'time',
        }
        if sep is None:
            sep = tail + head
        return head + sep.join(
            map(
                lambda (k, v): '{0}: {1}'.format(short_names[k], v),
                filter(
                    lambda (k, v): k in short_names,
                    self.info.items()
                )
            )
        ) + tail

    def format_info(self, crlf=True):
        return self.__symbol

    def format_table(self, align=u'LEFT', bgcolor=u'white'):
        return u'<TR><TD ALIGN="{0}" BGCOLOR="{1}">{2}</TD></TR>'.format(
            align,
            bgcolor,
            self.__symbol
        )

    def get_reliability(self):
        return 1.0

    def get_info(self, crlf=False):
        return dict()


class TokenBase(object):
    def __init__(self, info):
        if isinstance(info, dict):
            self.__term = Term(info)
        else:
            self.__term = Term(info.__term)

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

    def get_pos(self):
        return self.term().get_property('parts_of_speech', 'ro')

    def get_case(self):
        return self.term().get_property('case', 'ro')

    def get_gender(self):
        return self.term().get_property('gender', 'ro')

    def get_count(self):
        return self.term().get_property('count'), 'ro'

    def get_time(self):
        return self.term().get_property('time', 'ro')

    def get_word(self):
        return self.term().get_property('word', 'ro')


class TermWriteOnceMethods(object):
    def get_position(self):
        return self.term().get_property('position', 'w_once')

    def get_uniq(self):
        return self.term().get_property('uniq', 'w_once')


class TermCtxMethods(object):
    def get_reliability(self):
        return self.term().get_property('reliability', 'ctx')


class Token(TokenBase, TermRoMethods, TermWriteOnceMethods, TermCtxMethods):
    def __init__(self, based_on):
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
            self.__init_from_wordform(based_on)

    def __init_from_params(self, word, original_word, info, pos, uniq):
        TokenBase.__init__(
            self,
            dict(list(info.items()) + [('word', word), ])
        )
        self.term().add_property('original_word', 'w_once', original_word)
        self.term().add_property('position', 'w_once', pos)
        self.term().add_property('uniq', 'w_once', uniq)
        self.term().add_property('reliability', 'ctx', 1.0)

    def __init_from_wordform(self, token):
        TokenBase.__init__(self, token)

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


class WordForms(object):
    def __init__(self, word, forms):
        self.__word = word
        self.__forms = forms

    def get_forms(self):
        return self.__forms

    def get_word(self):
        return self.__word


class SpecStateIniForm(Token):
    def __init__(self):
        super(SpecStateIniForm, self).__init__(
            ns(
                word=u'ini',
                original_word=u'ini',
                info={'parts_of_speech': u'ini'},
                pos=None,
                uniq=0
            )
        )


class SpecStateFiniForm(Token):
    def __init__(self):
        super(SpecStateFiniForm, self).__init__(
            ns(
                word=u'fini',
                original_word=u'fini',
                info={'parts_of_speech': u'fini'},
                pos=None,
                uniq=0
            )
        )


class SpecStateVirtForm(object):
    def __init__(self, owner):
        self.__owner = owner

    def get_word(self):
        w = self.__owner.get_aggregated_word()
        if w:
            return w
        return u'virt_' + unicode(uuid.uuid1())

    def get_info(self):
        return self.__owner.get_aggregated_info()

    def get_pos(self):
        info = self.__owner.get_aggregated_info()
        return info['parts_of_speech'] if info.has_key('parts_of_speech') else 'virt'

    def get_position(self):
        positions = self.__owner.get_positions()
        return None if not positions else positions[0]

    def get_uniq(self):
        return self.__owner.get_aggregated_uniq()

    def get_reliability(self):
        return 1.0

    def export_dict(self):
        return {
            'name': 'virt',
            'reliability': 1.0,
            'hidden': True,
            'anchor': False,
            'form': {},
        }

    def __format_info(self, sep=None, head='', tail=''):
        short_names = {
            'parts_of_speech': 'pos',
            'case': 'case',
            'gender': 'gender',
            'count': 'count',
            'time': 'time',
        }
        if sep is None:
            sep = tail + head
        return head + sep.join(
            map(
                lambda (k, v): '{0}: {1}'.format(short_names[k], v),
                filter(
                    lambda (k, v): k in short_names,
                    self.__owner.get_aggregated_info().items()
                )
            )
        ) + tail

    def format_table(self, align=u'LEFT', bgcolor=u'white'):
        if self.__owner.get_aggregated_info() is None:
            return u'<TR><TD ALIGN="{0}" BGCOLOR="{1}">{2}</TD></TR>'.format(
                align,
                bgcolor,
                u'virt'
            )
        return self.__format_info(
            head=u'<TR><TD ALIGN="{0}" BGCOLOR="{1}">'.format(align, bgcolor),
            tail='</TD></TR>'
        )


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
        se = SyntaxEntry(symbol, symbol, position, self.__form_uniq)
        wf = WordForms(symbol, [se, ])
        self.__form_uniq = str(uuid.uuid1())
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
