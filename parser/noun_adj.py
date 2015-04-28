#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher


class RuleGender(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'noun-adj_gender', false_is_final=True)

    def apply_cb(self, mt, noun, adj):
        try:
            if noun.get_gender() != adj.get_gender():
                return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
            return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class RuleCount(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'noun-adj_count', false_is_final=True)

    def apply_cb(self, mt, noun, adj):
        try:
            if noun.get_count() != adj.get_count():
                return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
            return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class RuleCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'noun-adj_case', false_is_final=True)

    def apply_cb(self, mt, noun, adj):
        try:
            if noun.get_case() != adj.get_case():
                return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
            return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class RuleFinal(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'noun-adj_final', false_is_final=True, true_is_final=True, apply_if_all=['noun-adj_gender', 'noun-adj_count', 'noun-adj_case'])

    def apply_cb(self, mt, noun, adj):
        return matcher.PosMatchRes(matcher.PosMatchRes.dependentFalse)


class NounAdjectiveMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'noun', 'adj', default_res=matcher.PosMatchRes(matcher.PosMatchRes.defaultTrue))
        self.add_rule(RuleGender())
        self.add_rule(RuleCount())
        self.add_rule(RuleCase())
        self.add_rule(RuleFinal())

    def __noun_adj(self, wf1, wf2):
        if wf1.get_pos() == 'noun':
            return wf1, wf2
        return wf2, wf1

    def match(self, wf1, wf2):
        noun, adj = self.__noun_adj(wf1, wf2)

        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(noun, adj)
