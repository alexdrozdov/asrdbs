#!/usr/bin/env python
# -*- #coding: utf8 -*-


import worddb.worddb
import matcher
import noun_adj
import noun_noun
import preposition_noun
import verb_adverb
import verb_noun
import verb_pronoun
import verb_verb


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
        self.add_matcher(preposition_noun.PrepositionNounMatcher())
        self.add_matcher(verb_adverb.VerbAdverbMatcher())
        self.add_matcher(verb_noun.VerbNounMatcher())
        self.add_matcher(verb_noun.NounVerbMatcher())
        self.add_matcher(verb_pronoun.VerbPronounMatcher())
        self.add_matcher(verb_pronoun.PronounVerbMatcher())
        self.add_matcher(verb_verb.VerbVerbMatcher())

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
                print "\t\t\tApplyed", s
            else:
                print "\t\t\tDismissed", s


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

    def get_pos(self):
        return self.info['parts_of_speech']

    def get_case(self):
        return self.info['case']

    def get_gender(self):
        return self.info['gender']

    def get_count(self):
        return self.info['count']

    def get_time(self):
        return self.info['time']

    def get_word(self):
        return self.form['word']

    def format_info(self):
        res = ""
        if self.info.has_key('parts_of_speech'):
            res += " pos: " + self.info['parts_of_speech']
        if self.info.has_key('case'):
            res += " case: " + self.info['case']
        if self.info.has_key('gender'):
            res += " gender: " + self.info['gender']
        if self.info.has_key('count'):
            res += " count: " + self.info['count']
        if self.info.has_key('time'):
            res += " time: " + self.info['time']
        return res

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


class WordForm(WordFormInfo):
    def __init__(self, form, primary, pos):
        WordFormInfo.__init__(self, form, primary)
        self.__masters = []
        self.__slaves = []
        self.__pos = pos

    def link(self, slave, rule):
        self.__slaves.append((slave, rule))
        slave.__masters.append((self, rule))

    def get_master_count(self):
        return len(self.__masters)

    def get_position(self):
        return self.__pos


class WordForms(object):
    def __init__(self, form_matcher, forms):
        self.__fm = form_matcher
        self.__forms = forms

    def match(self, other_wfs):
        for my_wf in self.__forms:
            print "\tUsing", my_wf.get_word(), my_wf.format_info()
            for other_wf in other_wfs.__forms:
                print "\t\tMatching with", other_wf.get_word(), other_wf.format_info()
                self.__fm.match(my_wf, other_wf)


class WordFormFabric(object):
    def __init__(self, worddb_file):
        self.__wdb = worddb.worddb.Worddb(worddb_file)
        self.__fm = FormMatcher()

    def create(self, word, position):
        res = []
        info = self.__wdb.get_word_info(word)
        self.variants = []
        for i in info:
            form = i['form']
            primary = i['primary']
            for f in form:
                res.append(WordForm(f, primary, position))
        return WordForms(self.__fm, res)


class SentenceParser(object):
    def __init__(self, worddb_file):
        self.__wff = WordFormFabric(worddb_file)

    def parse(self, sentence):
        entries = []
        word_position = 0
        for w in sentence:
            wfs = self.__wff.create(w, word_position)
            print "Processing", w
            for e in entries:
                wfs.match(e)
            entries.append(wfs)
            word_position += 1

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
