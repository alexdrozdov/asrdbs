#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher
from matcher import defaultTrue, possibleTrue


class RuleTimeCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'verb-noun_inf-nom', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, verb, noun):
        return matcher.PosMatchRes(possibleTrue())


class VerbAdverbMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'verb', 'adverb', default_res=matcher.PosMatchRes(defaultTrue()))
        self.add_rule(RuleTimeCase())

    def __verb_adverb(self, wl1, wl2):
        if wl1.get_pos() == 'verb':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__verb_adverb(wf1, wf2)

    def match(self, verb, adverb):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(verb, adverb)
