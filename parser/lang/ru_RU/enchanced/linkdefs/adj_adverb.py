#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.matchcmn import independentFalse, defaultTrue, possibleTrue, PosMatchRule, PosMatcher


class RulePos(PosMatchRule):
    def __init__(self):
        super(RulePos, self).__init__('adj-adverb_pos', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, adj, adverb):
        if adj.get_position() - adverb.get_position() > 0:
            return possibleTrue(self.get_name())
        return independentFalse(self.get_name())


class AdjAdverbMatcher(PosMatcher):
    def __init__(self):
        super(AdjAdverbMatcher, self).__init__('adjective', 'adverb', default_res=defaultTrue())
        self.add_rule(RulePos())
