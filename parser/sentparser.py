#!/usr/bin/env python
# -*- #coding: utf8 -*-


import uuid
import re
import traceback
import worddb.worddb
from argparse import Namespace as ns


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


class WordFormInfo(object):
    def __init__(self, word, info):
        self.word = word
        self.info = info

    def is_adjective(self):
        return self.info['parts_of_speech'] == 'adjective'

    def is_noun(self):
        return self.info['parts_of_speech'] == 'noun'

    def is_verb(self):
        return self.info['parts_of_speech'] == 'verb'

    def is_adverb(self):
        return self.info['parts_of_speech'] == 'adverb'

    def is_pronoun(self):
        return self.info['parts_of_speech'] == 'pronoun'

    def is_preposition(self):
        return self.info['parts_of_speech'] == 'preposition'

    def get_pos(self):
        return self.info['parts_of_speech']

    def __get_info_param(self, name):
        try:
            return self.info[name]
        except KeyError:
            raise KeyError(u"Key {0} not found in info for {1}, {2}".format(
                name,
                self.info,
                self.get_word()
            ))

    def get_case(self):
        return self.__get_info_param('case')

    def get_gender(self):
        return self.__get_info_param('gender')

    def get_count(self):
        return self.__get_info_param('count')

    def get_time(self):
        return self.__get_info_param('time')

    def get_word(self):
        return self.word

    def has_tag(self, tag):
        return False

    def add_tag(self, tag, value=None):
        pass

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

    def format_info(self, crlf=False):
        sep = '\r\n' if crlf else ' '
        return self.__format_info(sep=sep)

    def format_table(self, align=u'LEFT', bgcolor=u'white'):
        return self.__format_info(
            head=u'<TR><TD ALIGN="{0}" BGCOLOR="{1}">'.format(align, bgcolor),
            tail='</TD></TR>'
        )

    def get_info(self, crlf=False):
        return self.info

    def __repr__(self):
        return "WordFormInfo(word='{0}')".format(self.get_word().encode('utf8'))

    def __str__(self):
        return "WordFormInfo(word='{0}')".format(self.get_word().encode('utf8'))


class Link(object):
    def __init__(self, rule, master, slave, uniq=None):
        self.__rule = rule
        if uniq is None:
            self.__uniq = str(uuid.uuid1())
        else:
            self.__uniq = uniq
        self.__master = master
        self.__slave = slave

    def get_uniq(self):
        return self.__uniq

    def get_rule(self):
        return self.__rule

    def get_master(self):
        return self.__master

    def get_slave(self):
        return self.__slave

    def set_ms(self, master, slave):
        self.__master = master
        self.__slave = slave


class WordForm(WordFormInfo, SentenceEntry):
    def __init__(self, based_on):
        assert isinstance(based_on, ns) or isinstance(based_on, WordForm)
        if isinstance(based_on, ns):
            self.__init_from_params(based_on.word, based_on.original_word, based_on.info, based_on.pos, based_on.uniq)
        else:
            self.__init_from_wordform(based_on)

    def __init_from_params(self, word, original_word, info, pos, uniq):
        WordFormInfo.__init__(self, word, info)
        SentenceEntry.__init__(self, original_word=original_word, is_word=True)
        self.__pos = pos
        self.__uniq = uniq

    def __init_from_wordform(self, wf):
        WordFormInfo.__init__(self, wf.get_word(), wf.get_info())
        SentenceEntry.__init__(self, original_word=wf.get_original(), is_word=wf.is_word())
        self.__pos = wf.pos
        self.__uniq = wf.__uniq

    def get_position(self):
        return self.__pos

    def get_uniq(self):
        return self.__uniq

    def get_reliability(self):
        return 1.0

    def __repr__(self):
        return "WordForm(word='{0}')".format(self.get_word().encode('utf8'))

    def __str__(self):
        return "WordForm(word='{0}')".format(self.get_word().encode('utf8'))


class WordForms(object):
    def __init__(self, word, forms, uniq):
        self.__word = word
        self.__forms = forms
        self.__uniq = uniq

    def get_forms(self):
        return self.__forms

    def get_word(self):
        return self.__word

    def get_uniq(self):
        return self.__uniq


class WordFormFabric(object):
    def __init__(self, worddb_file):
        self.__wdb = worddb.worddb.Worddb(worddb_file)
        self.__form_uniq = str(uuid.uuid1())
        self.__group_uniq = str(uuid.uuid1())

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
        wf = WordForms(symbol, [se, ], self.__group_uniq)
        self.__form_uniq = str(uuid.uuid1())
        self.__group_uniq = str(uuid.uuid1())
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
                WordForm(
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
        wf = WordForms(word, res, self.__group_uniq)
        self.__group_uniq = str(uuid.uuid1())
        return wf


class Tokenizer(object):
    def __init__(self):
        pass

    def tokenize(self, string):
        if isinstance(string, list):
            return string
        return filter(
            lambda s:
                s,
            re.sub(
                r'\.\s*$',
                r' . ',
                re.sub(
                    r"(,\s)",
                    r' \1',
                    re.sub(
                        r"([^\w\.\-\/,])",
                        r' \1 ',
                        string,
                        flags=re.U
                    ),
                    flags=re.U
                ),
                flags=re.U
            ).split()
        )


class TokenMapper(object):
    def __init__(self, worddb_file):
        self.__wff = WordFormFabric(worddb_file)

    def map(self, tokens):
        return map(
            lambda (word_pos, word): self.__wff.create(word, word_pos),
            enumerate(tokens)
        )
