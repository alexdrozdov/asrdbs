#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher
from matcher import independentFalse, dependentFalse, defaultFalse, invariantBool, defaultTrue, possibleTrue, reliableTrue


class RuleCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'pnoun-pnoun_case', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, wf1, wf2):
        try:
            if wf1.get_case() == 'nominative' and wf2.get_case() == 'nominative':
                return matcher.PosMatchRes(independentFalse())
            if wf2.get_case() == 'accusative':
                return matcher.PosMatchRes(independentFalse())
            if wf1.get_case() == 'nominative' and wf2.get_case() != 'nominative':
                return matcher.PosMatchRes(possibleTrue())
            if wf1.get_case() != 'nominative' and wf2.get_case() == 'nominative':
                return matcher.PosMatchRes(independentFalse())
                # if wf1.get_position() < wf2.get_position():
                #     return self.check_restricts(wf1, wf2)
                # return False
        except:
            pass
        return matcher.PosMatchRes(possibleTrue())


class NounPronounMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'noun', 'pronoun', default_res=matcher.PosMatchRes(defaultFalse()))
        self.add_rule(RuleCase())

    def __noun_pronoun(self, wl1, wl2):
        if wl1.get_pos() == 'noun':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__noun_pronoun(wf1, wf2)

    def match(self, wf1, wf2):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(wf1, wf2)


class PronounNounMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'pronoun', 'noun', default_res=matcher.PosMatchRes(defaultFalse()))
        self.add_rule(RuleCase())

    def __pronoun_noun(self, wl1, wl2):
        if wl1.get_pos() == 'pronoun':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__pronoun_noun(wf1, wf2)

    def match(self, wf1, wf2):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(wf1, wf2)

