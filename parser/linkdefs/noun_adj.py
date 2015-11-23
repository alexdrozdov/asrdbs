#!/usr/bin/env python
# -*- #coding: utf8 -*-


from parser.matchcmn import independentFalse, defaultTrue, possibleTrue, reliableTrue, PosMatchRule, PosMatcher


class RuleGender(PosMatchRule):
    def __init__(self):
        super(RuleGender, self).__init__('noun-adj_gender', false_is_final=True)

    def apply_cb(self, mt, noun, adj):
        try:
            if adj.get_count() != 'plural':
                if noun.get_gender() != adj.get_gender():
                    return independentFalse(self.get_name())
            return reliableTrue(self.get_name())
        except:
            pass
        return possibleTrue(self.get_name())


class RuleCount(PosMatchRule):
    def __init__(self):
        super(RuleCount, self).__init__('noun-adj_count', false_is_final=True)

    def apply_cb(self, mt, noun, adj):
        try:
            if noun.get_count() != adj.get_count():
                return independentFalse(self.get_name())
            return reliableTrue(self.get_name())
        except:
            pass
        return possibleTrue(self.get_name())


class RuleCase(PosMatchRule):
    def __init__(self):
        super(RuleCase, self).__init__('noun-adj_case', false_is_final=True)

    def apply_cb(self, mt, noun, adj):
        try:
            if noun.get_case() != adj.get_case():
                return independentFalse(self.get_name())
            return reliableTrue(self.get_name())
        except:
            pass
        return possibleTrue(self.get_name())


class RuleFinal(PosMatchRule):
    def __init__(self):
        super(RuleFinal, self).__init__(
            'noun-adj_final',
            false_is_final=True,
            true_is_final=True,
            apply_if_all=['noun-adj_gender', 'noun-adj_count', 'noun-adj_case']
        )

    def apply_cb(self, mt, noun, adj):
        return reliableTrue(self.get_name())


class NounAdjectiveMatcher(PosMatcher):
    def __init__(self):
        super(NounAdjectiveMatcher, self).__init__('noun', 'adjective', default_res=defaultTrue())
        self.add_rule(RuleGender())
        self.add_rule(RuleCount())
        self.add_rule(RuleCase())
        self.add_rule(RuleFinal())
