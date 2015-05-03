#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher


class RuleTime(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'noun-verb_case', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, v1, v2):
        try:
            if v1['time'] != v2['time'] and (v1['time'] == 'infinite' or v2['time'] == 'infinite'):
                return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
            return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class VerbVerbMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'verb', 'verb', default_res=matcher.PosMatchRes(matcher.PosMatchRes.defaultFalse))
        self.add_rule(RuleTime())

    def match(self, wf1, wf2):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(wf1, wf2)
