#!/usr/bin/env python
# -*- #coding: utf8 -*-


import json


class MatchBool(object):
    independentFalse = -3
    dependentFalse = -2
    defaultFalse = -1
    invariantBool = 0
    defaultTrue = 1
    possibleTrue = 2
    reliableTrue = 3

    def __init__(self, b):
        self.b = b

    def to_str(self):
        if self.b == MatchBool.independentFalse:
            return "independentFalse"
        if self.b == MatchBool.dependentFalse:
            return "dependentFalse"
        if self.b == MatchBool.defaultFalse:
            return "defaultFalse"
        if self.b == MatchBool.invariantBool:
            return "invariantBool"
        if self.b == MatchBool.defaultTrue:
            return "defaultTrue"
        if self.b == MatchBool.possibleTrue:
            return "possibleTrue"
        if self.b == MatchBool.reliableTrue:
            return "reliableTrue"

    def is_false(self):
        return self.b < MatchBool.invariantBool

    def is_true(self):
        return self.b > MatchBool.invariantBool


class independentFalse(MatchBool):
    def __init__(self):
        MatchBool.__init__(self, MatchBool.independentFalse)


class dependentFalse(MatchBool):
    def __init__(self):
        MatchBool.__init__(self, MatchBool.dependentFalse)


class defaultFalse(MatchBool):
    def __init__(self):
        MatchBool.__init__(self, MatchBool.defaultFalse)


class invariantBool(MatchBool):
    def __init__(self):
        MatchBool.__init__(self, MatchBool.invariantBool)


class defaultTrue(MatchBool):
    def __init__(self):
        MatchBool.__init__(self, MatchBool.defaultTrue)


class possibleTrue(MatchBool):
    def __init__(self):
        MatchBool.__init__(self, MatchBool.possibleTrue)


class reliableTrue(MatchBool):
    def __init__(self):
        MatchBool.__init__(self, MatchBool.reliableTrue)


class PosMatcherSelector(object):
    def __init__(self):
        self.match_dict = {}

    def add_matcher(self, matcher):
        pos1_name, pos2_name = matcher.get_pos_names()
        self.__add_cmp(pos1_name, pos2_name, matcher)
        if pos1_name != pos2_name:
            self.__add_cmp(pos2_name, pos1_name, matcher)

    def __add_cmp(self, p1, p2, matcher):
        if self.match_dict.has_key(p1):
            d = self.match_dict[p1]
        else:
            d = self.match_dict[p1] = {}
        if d.has_key(p2):
            d[p2].append(matcher)
        else:
            d[p2] = [matcher, ]

    def get_matchers(self, pos1_name, pos2_name):
        try:
            return self.match_dict[pos1_name][pos2_name]
        except:
            return []


class PosMatchRes(object):
    def __init__(self, fixed_status, reliability=1.0, explain_str=None):
        self.__fixed_status = fixed_status
        self.__reliability = reliability
        self.__explain_str = explain_str if explain_str is not None else "{}"
        self.__dependent_reliability = None

    def is_false(self):
        return self.__fixed_status.is_false()

    def is_true(self):
        return self.__fixed_status.is_true()

    def get_private_reliability(self):
        return self.__reliability

    def get_dependent_reliability(self, method):
        if self.__dependent_reliability is not None:
            return self.__dependent_reliability
        self.__dependent_reliability = self.__reliability * self.__based_on_reliability(method)

    def __based_on_reliability(self, method):
        return 1.0

    def explain_str(self):
        return self.__explain_str

    def set_explain_str(self, explain_str):
        self.__explain_str = explain_str

    def get_fixed_status(self):
        return self.__fixed_status


class PosMatchRule(object):
    def __init__(self, name, false_is_final=False, true_is_final=False, apply_if_all=[], apply_if_none=[], apply_if_any=[]):
        self.__name = name
        self.__false_is_final = false_is_final
        self.__true_is_final = true_is_final
        self.__apply_if_all = apply_if_all
        self.__apply_if_none = apply_if_none
        self.__apply_if_any = apply_if_any

    def get_name(self):
        return self.__name

    def res_is_final(self, res):
        if res.is_false() and self.__false_is_final:
            return True
        if res.is_true() and self.__true_is_final:
            return True
        return False

    def apply(self, matcher, wf1, wf2):
        based_on = {"rule": self.__name}

        if len(self.__apply_if_all):
            __and = []
            for a in self.__apply_if_all:
                r_cmp = matcher.get_apply_res(a, wf1, wf2)
                __and.append(r_cmp.explain_str())
                if r_cmp.is_false():
                    based_on['all'] = __and
                    based_on['res'] = dependentFalse().to_str()
                    return PosMatchRes(dependentFalse(), explain_str=json.dumps(based_on))
            based_on['all'] = __and

        if len(self.__apply_if_none):
            __none = []
            for a in self.__apply_if_none:
                r_cmp = matcher.get_apply_res(a, wf1, wf2)
                __none.append(r_cmp.explain_str())
                if not r_cmp.is_false():
                    based_on['none'] = __none
                    based_on['res'] = dependentFalse().to_str()
                    return PosMatchRes(dependentFalse(), explain_str=json.dumps(based_on))
            based_on['none'] = __none

        if len(self.__apply_if_none):
            any_found = False
            __any = []
            for a in self.__apply_if_any:
                r_cmp = matcher.get_apply_res(a, wf1, wf2)
                __any.append(r_cmp.explain_str())
                if not r_cmp.is_false():
                    any_found = True
                    break

            if not any_found:
                based_on['any'] = __any
                based_on['res'] = dependentFalse().to_str()
                return PosMatchRes(dependentFalse(), explain_str=json.dumps(based_on))

        r = self.apply_cb(matcher, wf1, wf2)
        based_on['res'] = r.get_fixed_status().to_str()
        r.set_explain_str(json.dumps(based_on))
        return r


class PosMatcher(object):
    def __init__(self, pos1_name, pos2_name, default_res=None):
        self.__pos1_name = pos1_name
        self.__pos2_name = pos2_name
        self.__name = self.__pos1_name + "_" + self.__pos2_name
        self.__rules = {}
        self.__default_res = default_res

    def get_pos_names(self):
        return (self.__pos1_name, self.__pos2_name)

    def get_name(self):
        return self.__name

    def add_rule(self, rule):
        self.__rules[rule.get_name()] = rule

    def get_rule(self, rule_name):
        return self.__rules[rule_name]

    def get_rules_list(self):
        return self.__rules.keys()

    def get_default_res(self):
        return self.__default_res


class RuntimePosMatcher(object):
    def __init__(self, pos_matcher):
        self.__pm = pos_matcher
        self.__evaled = {}

    def get_apply_res(self, name, wf1, wf2):
        if self.__evaled.has_key(name):
            return self.__evaled[name]
        rule = self.__pm.get_rule(name)
        res = rule.apply(self, wf1, wf2)
        self.__evaled[name] = res
        return res

    def match(self, wf1, wf2):
        pos_master, pos_slave = self.__pm.pos_order(wf1, wf2)
        for rule_name in self.__pm.get_rules_list():
            rule = self.__pm.get_rule(rule_name)
            res = self.get_apply_res(rule_name, pos_master, pos_slave)
            if rule.res_is_final(res):
                return res, pos_master, pos_slave
        return self.__pm.get_default_res(), pos_master, pos_slave
