#!/usr/bin/env python
# -*- #coding: utf8 -*-


import traceback
from parser.matchcmn import independentFalse, defaultFalse, defaultTrue, possibleTrue, reliableTrue, PosMatchRule, PosMatcher


class RuleTimeCase(PosMatchRule):
    def __init__(self):
        super(RuleTimeCase, self).__init__('verb-noun_inf-nom', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, verb, noun):
        try:
            if noun.get_case() == 'nominative':
                return independentFalse(self.get_name())
            return reliableTrue(self.get_name())
        except:
            print traceback.format_exc()
        return possibleTrue(self.get_name())


class VerbNounMatcher(PosMatcher):
    def __init__(self):
        super(VerbNounMatcher, self).__init__('verb', 'noun', default_res=defaultTrue())
        self.add_rule(RuleTimeCase())


class RuleCase(PosMatchRule):
    def __init__(self):
        super(RuleCase, self).__init__('noun-verb_case-count', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, noun, verb):
        try:
            if noun.get_case() == 'nominative' and noun.get_count() == verb.get_count():
                return reliableTrue(self.get_name())
            return independentFalse(self.get_name())
        except:
            print traceback.format_exc()
        return possibleTrue(self.get_name())


class NounVerbMatcher(PosMatcher):
    def __init__(self):
        super(NounVerbMatcher, self).__init__('noun', 'verb', default_res=defaultFalse())
        self.add_rule(RuleCase())
