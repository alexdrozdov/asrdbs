#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.matchcmn import independentFalse, defaultTrue, possibleTrue, reliableTrue, PosMatchRule, PosMatcher


class RulePos(PosMatchRule):
    def __init__(self):
        super(RulePos, self).__init__('adj-noun_pos', false_is_final=True)

    def apply_cb(self, mt, adj, noun):
        if noun.get_position() - adj.get_position() > 0:
            return possibleTrue(self.get_name())
        return independentFalse(self.get_name())


class RuleCase(PosMatchRule):
    def __init__(self):
        super(RuleCase, self).__init__('noun_case', false_is_final=True)

    def apply_cb(self, mt, adj, noun):
        try:
            if noun.get_case() not in ['ablative', 'prepositional']:
                return independentFalse(self.get_name())
            return reliableTrue(self.get_name())
        except:
            pass
        return possibleTrue(self.get_name())


class RuleFinal(PosMatchRule):
    def __init__(self):
        super(RuleFinal, self).__init__(
            'adj-noun_final',
            false_is_final=True,
            true_is_final=True,
            apply_if_all=['adj-noun_pos', 'noun_case']
        )

    def apply_cb(self, mt, noun, adj):
        return reliableTrue(self.get_name())


class AdjectiveNounMatcher(PosMatcher):
    def __init__(self):
        super(AdjectiveNounMatcher, self).__init__('adjective', 'noun', default_res=defaultTrue())
        self.add_rule(RulePos())
        self.add_rule(RuleCase())
        self.add_rule(RuleFinal())
