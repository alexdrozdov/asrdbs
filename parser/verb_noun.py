#!/usr/bin/env python
# -*- #coding: utf8 -*-


import matcher


class RuleTimeCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'verb-noun_inf-nom', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, verb, noun):
        try:
            if (verb.get_time() in ['infinite', 'past']) and noun.get_case() == 'nominative':
                return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
            return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class VerbNounMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'verb', 'noun', default_res=matcher.PosMatchRes(matcher.PosMatchRes.defaultTrue))
        self.add_rule(RuleTimeCase())

    def __verb_noun(self, wl1, wl2):
        if wl1.get_pos() == 'verb':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__verb_noun(wf1, wf2)

    def match(self, verb, noun):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(verb, noun)


class RuleCase(matcher.PosMatchRule):
    def __init__(self):
        matcher.PosMatchRule.__init__(self, 'noun-verb_case', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, verb, noun):
        try:
            if noun.get_case() == 'nominative':
                return matcher.PosMatchRes(matcher.PosMatchRes.independentFalse)
            return matcher.PosMatchRes(matcher.PosMatchRes.reliableTrue)
        except:
            pass
        return matcher.PosMatchRes(matcher.PosMatchRes.possibleTrue)


class NounVerbMatcher(matcher.PosMatcher):
    def __init__(self):
        matcher.PosMatcher.__init__(self, 'noun', 'verb', default_res=matcher.PosMatchRes(matcher.PosMatchRes.defaultFalse))
        self.add_rule(RuleCase())

    def __noun_verb(self, wl1, wl2):
        if wl1.get_pos() == 'noun':
            return wl1, wl2
        return wl2, wl1

    def pos_order(self, wf1, wf2):
        return self.__noun_verb(wf1, wf2)

    def match(self, noun, verb):
        rt_matcher = matcher.RuntimePosMatcher(self)
        return rt_matcher.match(noun, verb)
