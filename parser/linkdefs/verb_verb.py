#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.matchcmn import independentFalse, defaultFalse, possibleTrue, reliableTrue, PosMatchRule, PosMatcher


class RuleTime(PosMatchRule):
    def __init__(self):
        super(RuleTime, self).__init__('verb-verb_case', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, v1, v2):
        try:
            if v1['time'] != v2['time'] and (v1['time'] == 'infinite' or v2['time'] == 'infinite'):
                return reliableTrue(self.get_name())
            return independentFalse(self.get_name())
        except:
            pass
        return possibleTrue(self.get_name())


class VerbVerbMatcher(PosMatcher):
    def __init__(self):
        super(VerbVerbMatcher, self).__init__('verb', 'verb', default_res=defaultFalse())
        self.add_rule(RuleTime())
