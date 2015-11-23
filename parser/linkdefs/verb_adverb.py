#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.matchcmn import defaultTrue, possibleTrue, PosMatchRule, PosMatcher


class RuleAny(PosMatchRule):
    def __init__(self):
        super(RuleAny, self).__init__('verb-noun_inf-nom', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, verb, noun):
        return possibleTrue(self.get_name())


class VerbAdverbMatcher(PosMatcher):
    def __init__(self):
        super(VerbAdverbMatcher, self).__init__('verb', 'adverb', default_res=defaultTrue())
        self.add_rule(RuleAny())
