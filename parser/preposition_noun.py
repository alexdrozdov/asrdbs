#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher
from matcher import independentFalse, defaultTrue, possibleTrue, reliableTrue


class RulePos(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'prep-noun_pos', false_is_final=True)

    def apply_cb(self, mt, prep, noun):
        if prep.get_position() > noun.get_position():
            return matcher.PosMatchRes(independentFalse())
        return matcher.PosMatchRes(reliableTrue())


class RuleCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'prep-noun_case', false_is_final=True)

    def apply_cb(self, mt, prep, noun):
        try:
            if prep.get_case() == noun.get_case():
                return matcher.PosMatchRes(reliableTrue())
            return matcher.PosMatchRes(independentFalse())
        except:
            pass
        return matcher.PosMatchRes(possibleTrue())


class RuleFinal(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'noun-adj_final', false_is_final=True, true_is_final=True, apply_if_all=['prep-noun_pos', 'prep-noun_case'])

    def __apply_cb(self, mt, noun, adj):
        return matcher.PosMatchRes(reliableTrue())

    def apply_cb(self, mt, noun, adj):
        r = self.__apply_cb(mt, noun, adj)
        return r


class PrepositionNounMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'preposition', 'noun', default_res=matcher.PosMatchRes(defaultTrue()))
        self.add_rule(RulePos())
        self.add_rule(RuleCase())
        self.add_rule(RuleFinal())

    def __preposition_noun(self, wf1, wf2):
        if wf1.get_pos() == 'preposition':
            return wf1, wf2
        return wf2, wf1

    def pos_order(self, wf1, wf2):
        return self.__preposition_noun(wf1, wf2)

    def match(self, prep, noun):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(prep, noun)
