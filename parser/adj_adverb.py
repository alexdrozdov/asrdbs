#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher
from matcher import independentFalse, defaultTrue, possibleTrue


class RulePos(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'adj-adverb_pos', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, adj, adverb):
        if adj.get_position() - adverb.get_position() == 1:
            return matcher.PosMatchRes(possibleTrue())
        return matcher.PosMatchRes(independentFalse())


class AdjAdverbMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'adjective', 'adverb', default_res=matcher.PosMatchRes(defaultTrue()))
        self.add_rule(RulePos())

    def __adj_adverb(self, wl1, wl2):
        if wl1.get_pos() == 'adjective':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__adj_adverb(wf1, wf2)

    def match(self, adj, adverb):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(adj, adverb)
