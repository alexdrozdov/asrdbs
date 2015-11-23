#!/usr/bin/env python
# -*- #coding: utf8 -*-


import traceback
from parser.matchcmn import independentFalse, defaultFalse, defaultTrue, possibleTrue, reliableTrue, PosMatchRule, PosMatcher


class RuleTimeCase(PosMatchRule):
    def __init__(self):
        super(RuleTimeCase, self).__init__('verb-pronoun_inf-nom', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, verb, pronoun):
        try:
            if pronoun.get_case() == 'nominative':
                return independentFalse(self.get_name())
            return reliableTrue(self.get_name())
        except:
            print traceback.format_exc()
        return possibleTrue(self.get_name())


class VerbPronounMatcher(PosMatcher):
    def __init__(self):
        super(VerbPronounMatcher, self).__init__('verb', 'pronoun', default_res=defaultTrue())
        self.add_rule(RuleTimeCase())


class RuleCase(PosMatchRule):
    def __init__(self):
        super(RuleCase, self).__init__('pronoun-verb_case-count', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, pronoun, verb):
        try:
            if pronoun.get_case() == 'nominative' and pronoun.get_count() == verb.get_count():
                return reliableTrue(self.get_name())
            return independentFalse(self.get_name())
        except:
            print traceback.format_exc()
        return possibleTrue(self.get_name())


class PronounVerbMatcher(PosMatcher):
    def __init__(self):
        super(PronounVerbMatcher, self).__init__('pronoun', 'verb', default_res=defaultFalse())
        self.add_rule(RuleCase())
