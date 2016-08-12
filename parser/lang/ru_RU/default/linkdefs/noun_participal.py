#!/usr/bin/env python
# -*- #coding: utf8 -*-


import traceback
from parser.matchcmn import independentFalse, defaultTrue, possibleTrue, reliableTrue, PosMatchRule, PosMatcher


class RuleGender(PosMatchRule):
    def __init__(self):
        super(RuleGender, self).__init__('noun-participal_gender', false_is_final=True)

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
        super(RuleCount, self).__init__('noun-participal_count', false_is_final=True)

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
        super(RuleCase, self).__init__('noun-participal_case', false_is_final=True)

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
            'noun-participal_final',
            false_is_final=True,
            true_is_final=True,
            apply_if_all=['noun-participal_gender', 'noun-participal_count', 'noun-participal_case']
        )

    def apply_cb(self, mt, noun, adj):
        return reliableTrue(self.get_name())


class NounParticipalMatcher(PosMatcher):
    def __init__(self):
        super(NounParticipalMatcher, self).__init__('noun', 'participal', default_res=defaultTrue())
        self.add_rule(RuleGender())
        self.add_rule(RuleCount())
        self.add_rule(RuleCase())
        self.add_rule(RuleFinal())


class RuleDependentCase(PosMatchRule):
    def __init__(self):
        super(RuleDependentCase, self).__init__('participal-noun_notnom', false_is_final=True, true_is_final=True)

    def apply_cb(self, mt, participal, noun):
        try:
            if noun.get_case() == 'nominative':
                return independentFalse(self.get_name())
            return reliableTrue(self.get_name())
        except:
            print(traceback.format_exc())
        return possibleTrue(self.get_name())


class ParticipalNounMatcher(PosMatcher):
    def __init__(self):
        super(ParticipalNounMatcher, self).__init__('participal', 'noun', default_res=defaultTrue())
        self.add_rule(RuleDependentCase())
