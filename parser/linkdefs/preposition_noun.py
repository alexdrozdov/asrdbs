#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.matchcmn import independentFalse, defaultTrue, possibleTrue, reliableTrue, PosMatchRule, PosMatcher


class RulePos(PosMatchRule):
    def __init__(self):
        super(RulePos, self).__init__('prep-noun_pos', false_is_final=True)

    def apply_cb(self, mt, prep, noun):
        if prep.get_position() > noun.get_position():
            return independentFalse(self.get_name())
        return reliableTrue(self.get_name())


class RuleCase(PosMatchRule):
    def __init__(self):
        super(RuleCase, self).__init__('prep-noun_case', false_is_final=True)

    def apply_cb(self, mt, prep, noun):
        try:
            if prep.get_case() == noun.get_case():
                return reliableTrue(self.get_name())
            return independentFalse(self.get_name())
        except:
            pass
        return possibleTrue(self.get_name())


class RuleFinal(PosMatchRule):
    def __init__(self):
        super(RuleFinal, self).__init__('noun-adj_final', false_is_final=True, true_is_final=True, apply_if_all=['prep-noun_pos', 'prep-noun_case'])

    def apply_cb(self, mt, noun, adj):
        return reliableTrue(self.get_name())


class PrepositionNounMatcher(PosMatcher):
    def __init__(self):
        super(PrepositionNounMatcher, self).__init__('preposition', 'noun', default_res=defaultTrue())
        self.add_rule(RulePos())
        self.add_rule(RuleCase())
        self.add_rule(RuleFinal())
