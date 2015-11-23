#!/usr/bin/env python
# -*- #coding: utf8 -*-


import traceback
from parser.matchcmn import independentFalse, defaultFalse, possibleTrue, PosMatchRule, PosMatcher


class RuleCase(PosMatchRule):
    def __init__(self):
        super(RuleCase, self).__init__('pnoun-pnoun_case', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, wf1, wf2):
        try:
            if wf1.get_case() == wf2.get_case():
                return possibleTrue(self.get_name())
            if wf2.get_case() == 'genitive':
                return possibleTrue(self.get_name())
            return independentFalse(self.get_name())
        except:
            print traceback.format_exc()
        return possibleTrue(self.get_name())


class NounPronounMatcher(PosMatcher):
    def __init__(self):
        super(NounPronounMatcher, self).__init__('noun', 'pronoun', default_res=defaultFalse())
        self.add_rule(RuleCase())


class PronounNounMatcher(PosMatcher):
    def __init__(self):
        super(PronounNounMatcher, self).__init__('pronoun', 'noun', default_res=defaultFalse())
        self.add_rule(RuleCase())
