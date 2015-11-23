#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.matchcmn import independentFalse, defaultFalse, possibleTrue, PosMatchRule, PosMatcher


class RuleCase(PosMatchRule):
    def __init__(self):
        super(RuleCase, self).__init__('noun-noun_case', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, wf1, wf2):
        try:
            if wf1.get_case() == 'nominative' and wf2.get_case() == 'nominative':
                return independentFalse(self.get_name())
            if wf2.get_case() == 'accusative':
                return independentFalse(self.get_name())
            if wf1.get_case() == 'nominative' and wf2.get_case() != 'nominative':
                return possibleTrue(self.get_name())
            if wf1.get_case() != 'nominative' and wf2.get_case() == 'nominative':
                return independentFalse(self.get_name())
        except:
            pass
        return possibleTrue(self.get_name())


class NounNounMatcher(PosMatcher):
    def __init__(self):
        super(NounNounMatcher, self).__init__('noun', 'noun', default_res=defaultFalse())
        self.add_rule(RuleCase())
