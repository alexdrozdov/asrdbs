#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matchcmn
import linkdefs.noun_adj
import linkdefs.noun_participal
import linkdefs.noun_noun
import linkdefs.noun_pronoun
import linkdefs.preposition_noun
import linkdefs.verb_adverb
import linkdefs.verb_noun
import linkdefs.verb_pronoun
import linkdefs.verb_verb
import linkdefs.adj_adverb


class WordMatcher(object):
    def __init__(self):
        self.match_dict = {}
        self.add_matcher(linkdefs.noun_adj.NounAdjectiveMatcher())
        self.add_matcher(linkdefs.noun_participal.NounParticipalMatcher())
        self.add_matcher(linkdefs.noun_noun.NounNounMatcher())
        self.add_matcher(linkdefs.noun_pronoun.NounPronounMatcher())
        self.add_matcher(linkdefs.preposition_noun.PrepositionNounMatcher())
        self.add_matcher(linkdefs.verb_adverb.VerbAdverbMatcher())
        self.add_matcher(linkdefs.verb_noun.VerbNounMatcher())
        self.add_matcher(linkdefs.verb_noun.NounVerbMatcher())
        self.add_matcher(linkdefs.verb_pronoun.VerbPronounMatcher())
        self.add_matcher(linkdefs.verb_pronoun.PronounVerbMatcher())
        self.add_matcher(linkdefs.verb_verb.VerbVerbMatcher())
        self.add_matcher(linkdefs.adj_adverb.AdjAdverbMatcher())

    def add_matcher(self, matcher):
        pos1_name, pos2_name = matcher.get_pos_names()
        self.__add_cmp(pos1_name, pos2_name, matcher)

    def __add_cmp(self, p1, p2, matcher):
        if self.match_dict.has_key(p1):
            d = self.match_dict[p1]
        else:
            d = self.match_dict[p1] = {}
        if d.has_key(p2):
            d[p2].append(matcher)
        else:
            d[p2] = [matcher, ]

    def get_matchers(self, pos1_name, pos2_name):
        try:
            return self.match_dict[pos1_name][pos2_name]
        except:
            return []

    def match(self, wf1, wf2):
        for m in self.get_matchers(wf1.get_pos(), wf2.get_pos()):
            return m.match(wf1, wf2)
        return matchcmn.invariantBool()


matcher = WordMatcher()
