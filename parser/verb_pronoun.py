#!/usr/bin/env python
# -*- #coding: utf8 -*-


import traceback
import matcher
from matcher import independentFalse, defaultFalse, defaultTrue, possibleTrue, reliableTrue


class RuleTimeCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'verb-pronoun_inf-nom', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, verb, pronoun):
        try:
            if pronoun.get_case() == 'nominative':
                return matcher.PosMatchRes(independentFalse())
            return matcher.PosMatchRes(reliableTrue())
        except:
            print traceback.format_exc()
        return matcher.PosMatchRes(possibleTrue)


class VerbPronounMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'verb', 'pronoun', default_res=matcher.PosMatchRes(defaultTrue()))
        self.add_rule(RuleTimeCase())

    def __verb_pronoun(self, wl1, wl2):
        if wl1.get_pos() == 'verb':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__verb_pronoun(wf1, wf2)

    def match(self, verb, pronoun):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(verb, pronoun)


class RuleCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'pronoun-verb_case-count', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, pronoun, verb):
        try:
            if pronoun.get_case() == 'nominative' and pronoun.get_count() == verb.get_count():
                return matcher.PosMatchRes(reliableTrue())
            return matcher.PosMatchRes(independentFalse())
        except:
            print traceback.format_exc()
        return matcher.PosMatchRes(possibleTrue())


class PronounVerbMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'pronoun', 'verb', default_res=matcher.PosMatchRes(defaultFalse()))
        self.add_rule(RuleCase())

    def __pronoun_verb(self, wl1, wl2):
        if wl1.get_pos() == 'pronoun':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__pronoun_verb(wf1, wf2)

    def match(self, pronoun, verb):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(pronoun, verb)
