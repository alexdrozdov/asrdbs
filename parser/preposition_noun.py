#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher


class RulePos(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'prep-noun_pos', false_is_final=True)

    def apply_cb(self, mt, prep, noun):
        if prep.get_position() > noun.get_position():
            return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
        try:
            if prep.get_case() == noun.get_case():
                return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class RuleCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'prep-noun_case', false_is_final=True)

    def apply_cb(self, mt, prep, noun):
        if prep.get_position() > noun.get_position():
            return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
        try:
            if prep.get_case() == noun.get_case():
                return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class PrepositionNounMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'noun', 'noun', default_res=matcher.PosMatchRes(matcher.PosMatchRes.defaultTrue))
        self.add_rule(RulePos())

    def __preposition_noun(self, wf1, wf2):
        if wf1.get_pos() == 'preposition':
            return wf1, wf2
        return wf2, wf1

    def match(self, wf1, wf2):
        prep, noun = self.__preposition_noun(wf1, wf2)

        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(prep, noun)
