#!/usr/bin/env python
# -*- #coding: utf8 -*-


import traceback
import worddb.worddb
import matcher
import noun_adj
import noun_noun
import noun_pronoun
import preposition_noun
import verb_adverb
import verb_noun
import verb_pronoun
import verb_verb
import adj_adverb


class UniqEnum(object):
    def __init__(self):
        self.__uniq = 1

    def get_uniq(self):
        r = self.__uniq
        self.__uniq *= 2
        return r


ue = UniqEnum()


class SentenceEntry(object):

    word = 1
    syntax = 2

    def __init__(self, is_word=False, is_syntax=False):
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


class SyntaxEntry(SentenceEntry):
    def __init__(self, symbol, position, uniq):
        SentenceEntry.__init__(self, is_syntax=True)
        self.__symbol = symbol
        self.__pos = position
        self.__uniq = uniq
        self.__group = None

    def clone_without_links(self):
        return SyntaxEntry(self.__symbol, self.__pos, self.__uniq)

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

    def set_group(self, group):
        self.__group = group

    def get_slaves(self):
        return []

    def get_group(self):
        return self.__group

    def get_masters(self):
        return []

    def format_info(self, crlf=True):
        return self.__symbol

    def has_links(self):
        return False


class ConflictResolver(object):
    def __init__(self):
        pass

    def add(self, wf):
        pass


conflict_resolver = ConflictResolver()


class FormMatcher(matcher.PosMatcherSelector):
    def __init__(self):
        matcher.PosMatcherSelector.__init__(self)
        self.add_matcher(noun_adj.NounAdjectiveMatcher())
        self.add_matcher(noun_noun.NounNounMatcher())
        self.add_matcher(noun_noun.NounNounRMatcher())
        self.add_matcher(noun_pronoun.NounPronounMatcher())
        # self.add_matcher(noun_pronoun.PronounNounMatcher())
        self.add_matcher(preposition_noun.PrepositionNounMatcher())
        self.add_matcher(verb_adverb.VerbAdverbMatcher())
        self.add_matcher(verb_noun.VerbNounMatcher())
        self.add_matcher(verb_noun.NounVerbMatcher())
        self.add_matcher(verb_pronoun.VerbPronounMatcher())
        self.add_matcher(verb_pronoun.PronounVerbMatcher())
        self.add_matcher(verb_verb.VerbVerbMatcher())
        self.add_matcher(adj_adverb.AdjAdverbMatcher())

    def match(self, wf1, wf2):
        matchers = self.get_matchers(wf1.get_pos(), wf2.get_pos())
        for m in matchers:
            res, master, slave = m.match(wf1, wf2)
            s = '{0} {1} {2}'.format(type(m), m.get_pos_names(), res.explain_str())
            if res.is_true():
                master.link(slave, res)
                if slave.get_master_count() > 1:
                    conflict_resolver.add(slave)
                    s = ' [CONFLICT]' + s
                # print "\t\t\tApplyed", s
            # else:
                # print "\t\t\tDismissed", s


class AdverbAdjective(object):
    def __init__(self):
        pass

    def compare(self, info1, info2):
        return True


class WordFormInfo(object):
    def __init__(self, form, primary):
        self.form = form
        self.primary = primary
        self.info = eval(self.form['info'])

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
        except KeyError as e:
            print u"Key ", name, u" not found in info for", self.info, self.get_word()
            traceback.format_exc()
            raise e

    def get_case(self):
        return self.__get_info_param('case')

    def get_gender(self):
        return self.__get_info_param('gender')

    def get_count(self):
        return self.__get_info_param('count')

    def get_time(self):
        return self.__get_info_param('time')

    def get_word(self):
        return self.form['word']

    def has_property(self, prop_name):
        return self.info.has_key(prop_name)

    def format_info(self, crlf=False):
        res = ""
        if self.info.has_key('parts_of_speech'):
            res += " pos: " + self.info['parts_of_speech']
            if crlf:
                res += "\r\n"
        if self.info.has_key('case'):
            res += " case: " + self.info['case']
            if crlf:
                res += "\r\n"
        if self.info.has_key('gender'):
            res += " gender: " + self.info['gender']
            if crlf:
                res += "\r\n"
        if self.info.has_key('count'):
            res += " count: " + self.info['count']
            if crlf:
                res += "\r\n"
        if self.info.has_key('time'):
            res += " time: " + self.info['time']
            if crlf:
                res += "\r\n"
        return res

    def get_info(self, crlf=False):
        res = ""
        if self.info.has_key('parts_of_speech'):
            res += " pos: " + self.info['parts_of_speech']
            if crlf:
                res += ","
        if self.info.has_key('case'):
            res += " case: " + self.info['case']
            if crlf:
                res += ","
        if self.info.has_key('gender'):
            res += " gender: " + self.info['gender']
            if crlf:
                res += ","
        if self.info.has_key('count'):
            res += " count: " + self.info['count']
            if crlf:
                res += ","
        if self.info.has_key('time'):
            res += " time: " + self.info['time']
        return res

    def is_subject(self):
        return self.info.has_key('parts_of_speech') and self.info.has_key('case') and self.info['parts_of_speech'] == 'noun' and self.info['case'] == 'nominative'

    def is_predicate(self):
        return self.info.has_key('parts_of_speech') and self.info['parts_of_speech'] == 'verb'

    def spec_cmp(self, spec, ignore_missing=False):
        for k, v in spec.items():
            if self.info.has_key(k):
                if self.info[k] == v:
                    continue
                return False
            if ignore_missing:
                continue
            return False
        return True

    def __repr__(self):
        return "WordFormInfo(word='{0}')".format(self.get_word().encode('utf8'))

    def __str__(self):
        return "WordFormInfo(word='{0}')".format(self.get_word().encode('utf8'))


class Link(object):
    def __init__(self, rule, master, slave, uniq=None):
        self.__rule = rule
        if uniq is None:
            self.__uniq = ue.get_uniq()
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

    def clone_without_links(self):
        return Link(self.__rule, None, None, uniq=self.get_uniq())

    def unlink(self):
        pass


class WordForm(WordFormInfo, SentenceEntry):
    def __init__(self, form, primary, pos, uniq):
        WordFormInfo.__init__(self, form, primary)
        SentenceEntry.__init__(self, is_word=True)
        self.__masters = []
        self.__slaves = []
        self.__pos = pos
        self.__group = None
        self.__uniq = uniq

    def link(self, slave, rule):
        l = Link(rule, self, slave)
        self.__slaves.append((slave, l))
        slave.__masters.append((self, l))

    def get_master_count(self):
        return len(self.__masters)

    def get_position(self):
        return self.__pos

    def get_slaves(self):
        return self.__slaves

    def get_masters(self):
        return self.__masters

    def get_master_forms(self):
        return [m for m, l in self.__masters]

    def get_slave_forms(self):
        return [s for s, l in self.__slaves]

    def set_group(self, group):
        self.__group = group

    def get_group(self):
        return self.__group

    def get_uniq(self):
        return self.__uniq

    def clone_without_links(self):
        return WordForm(self.form, self.primary, self.__pos, self.__uniq)

    def has_links(self):
        return (len(self.__slaves) + len(self.__masters)) > 0

    def get_links(self):
        r = []
        for l in self.__masters:
            r.append(l)
        for l in self.__slaves:
            r.append(l)
        return r

    def add_slave(self, link, slave):
        self.__slaves.append((slave, link))

    def add_master(self, link, master):
        self.__masters.append((master, link))

    def remove_master(self, master):
        masters = []
        for m, l in self.__masters:
            if master == m:
                continue
            masters.append((m, l))
        self.__masters = masters

    def remove_slave(self, slave):
        slaves = []
        for s, l in self.__slaves:
            if slave == s:
                continue
            slaves.append((s, l))
        self.__slaves = slaves

    def get_link_count(self):
        return len(self.__masters) + len(self.__slaves)

    def get_link_to(self, other):
        for m, l in self.__masters:
            if other == m:
                return l
        for s, l in self.__slaves:
            if other == s:
                return l
        return None

    def __repr__(self):
        return "WordForm(word='{0}')".format(self.get_word().encode('utf8'))

    def __str__(self):
        return "WordForm(word='{0}')".format(self.get_word().encode('utf8'))


class WordForms(object):
    def __init__(self, form_matcher, word, forms, uniq):
        self.__fm = form_matcher
        self.__word = word
        self.__forms = forms
        self.__uniq = uniq
        for f in self.__forms:
            f.set_group(self)

    def match(self, other_wfs):
        for my_wf in self.__forms:
            # print "\tUsing", my_wf.get_word(), my_wf.format_info()
            for other_wf in other_wfs.__forms:
                # print "\t\tMatching with", other_wf.get_word(), other_wf.format_info()
                self.__fm.match(my_wf, other_wf)

    def get_forms(self):
        return self.__forms

    def get_word(self):
        return self.__word

    def get_uniq(self):
        return self.__uniq


class WordFormFabric(object):
    def __init__(self, worddb_file):
        self.__wdb = worddb.worddb.Worddb(worddb_file)
        self.__fm = FormMatcher()
        self.__form_uniq = 1
        self.__group_uniq = 1

    def create(self, word, position):
        if word in '.,;-!?':
            return self.__create_syntax_entry(word, position)
        return self.__create_word_form(word, position)

    def __create_syntax_entry(self, symbol, position):
        se = SyntaxEntry(symbol, position, self.__form_uniq)
        wf = WordForms(self.__fm, symbol, [se, ], self.__group_uniq)
        self.__form_uniq *= 2
        self.__group_uniq *= 2
        return wf

    def __validate_info(self, info):
        try:
            info = eval(info['info'])
            if info['parts_of_speech'] == 'noun' or info['parts_of_speech'] == 'pronoun' or info['parts_of_speech'] == 'adjective':
                if info.has_key('case') and info.has_key('count'):  # and info.has_key('gender'):
                    return True
                print info.has_key('case'), info.has_key('count'), info.has_key('gender'), info
                return False
            return True
        except:
            print "Info validation failed for", info
            print traceback.format_exc()
            return False

    def __create_word_form(self, word, position):
        res = []
        info = self.__wdb.get_word_info(word)
        if info is None:
            print word
            raise ValueError(u"No info avaible for " + word)
        self.variants = []
        for i in info:
            form = i['form']
            primary = i['primary']
            for f in form:
                if not self.__validate_info(f):
                    continue
                res.append(WordForm(f, primary, position, self.__form_uniq))
                self.__form_uniq *= 2
        wf = WordForms(self.__fm, word, res, self.__group_uniq)
        self.__group_uniq *= 2
        return wf


class SentenceParser(object):
    def __init__(self, worddb_file):
        self.__wff = WordFormFabric(worddb_file)

    def parse(self, sentence):
        entries = []
        word_position = 0
        for w in sentence:
            wfs = self.__wff.create(w, word_position)
            # print "Processing", w
            for e in entries:
                wfs.match(e)
            entries.append(wfs)
            word_position += 1

        return entries

    def validate_complete_attraction(self):
        for e in self.entries:
            if not e.has_attractions():
                return False
        return True

    def validate_group_linkage(self):
        unknown = [e for e in self.entries[1:]]
        accessable = [self.entries[0]]
        finalized = []
        while len(accessable) > 0:
            e = accessable.pop()
            acc = e.get_accessable_groups()
            for a in acc:
                if a not in unknown:
                    continue
                accessable.append(a)
                unknown.remove(a)
            finalized.append(e)
        if len(unknown) > 0:
            return False
        return True

    def attract(self):
        for e in self.entries:
            for ee in self.entries:
                if e != ee:
                    e.check_attract(ee)
