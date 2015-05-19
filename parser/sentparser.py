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


class UniqEnum(object):
    def __init__(self):
        self.__uniq = 1

    def get_uniq(self):
        r = self.__uniq
        self.__uniq *= 2
        return r


ue = UniqEnum()


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


class Link(object):
    def __init__(self, rule):
        self.__rule = rule
        self.__uniq = ue.get_uniq()

    def get_uniq(self):
        return self.__uniq

    def get_rule(self):
        return self.__rule


class WordForm(WordFormInfo):
    def __init__(self, form, primary, pos, uniq):
        WordFormInfo.__init__(self, form, primary)
        self.__masters = []
        self.__slaves = []
        self.__pos = pos
        self.__group = None
        self.__uniq = uniq

    def link(self, slave, rule):
        l = Link(rule)
        self.__slaves.append((slave, l))
        slave.__masters.append((self, l))

    def get_master_count(self):
        return len(self.__masters)

    def get_position(self):
        return self.__pos

    def get_slaves(self):
        return self.__slaves

    def set_group(self, group):
        self.__group = group

    def get_group(self):
        return self.__group

    def get_uniq(self):
        return self.__uniq

    def has_links(self):
        return (len(self.__slaves) + len(self.__masters)) > 0

    def get_links(self):
        r = []
        for l in self.__masters:
            r.append(l)
        for l in self.__slaves:
            r.append(l)
        return r


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
        res = []
        info = self.__wdb.get_word_info(word)
        self.variants = []
        for i in info:
            form = i['form']
            primary = i['primary']
            for f in form:
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
