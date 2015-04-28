#!/usr/bin/env python
# -*- #coding: utf8 -*-


import json


class BasedOn(object):
    def __init__(self, term_name):
        self.__term_name = term_name
        self.__and = []
        self.__none = []
        self.__any = []
        self.__special = []

        self.__current = None
        self.__res = PosMatchRes.invariantBool

    def term_start_and(self):
        self.__current = self.__and

    def term_start_none(self):
        self.__current = self.__none

    def term_start_any(self):
        self.__current = self.__any

    def term_start_special(self):
        self.__current = self.__special

    def term_finish(self):
        self.__current = None

    def add_term(self, term_str):
        self.__current.append(term_str)

    def to_str(self):
        res = {}
        r = {}
        if len(self.__and):
            r['and'] = self.__and
        if len(self.__none):
            r['none'] = self.__none
        if len(self.__any):
            r['any'] = self.__any
        if len(self.__spec):
            r['spec'] = self.__special
        r['res'] = PosMatchRes.to_str(self.__res)
        res = {self.__term_name: r}
        return json.dumps(res)


class PosMatcherSelector(object):
    def __init__(self):
        self.match_dict = {}

    def add_matcher(self, matcher):
        pos1_name, pos2_name = matcher.get_pos_names()
        self.__add_cmp(pos1_name, pos2_name, matcher)
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
    independentFalse = -3
    dependentFalse = -2
    defaultFalse = -1
    invariantBool = 0
    defaultTrue = 1
    possibleTrue = 2
    reliableTrue = 3

    def __init__(self, fixed_status, reliability=1.0, based_on=''):
        self.__fixed_status = fixed_status
        self.__reliability = reliability
        self.__based_on = based_on
        self.__dependent_reliability = None

    def is_false(self):
        return self.__fixed_status < PosMatchRes.invariantBool

    def is_true(self):
        return self.__fixed_status > PosMatchRes.invariantBool

    def get_private_reliability(self):
        return self.__reliability

    def get_dependent_reliability(self, method):
        if self.__dependent_reliability is not None:
            return self.__dependent_reliability
        self.__dependent_reliability = self.__reliability * self.__based_on_reliability(method)

    def __based_on_reliability(self, method):
        return 1.0

    def based_on(self):
        return self.__based_on


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
        return True

    def apply(self, matcher, wf1, wf2):
        based_on = BasedOn(self.__name)

        based_on.term_start_and()
        for a in self.__apply_if_all:
            r_cmp = matcher.get_apply_res(a, wf1, wf2)
            based_on.add_term(r_cmp.explain_str())
            if r_cmp.is_false():
                return PosMatchRes(PosMatchRes.dependentFalse, based_on=based_on)

        based_on.term_start_none()
        for a in self.__apply_if_none:
            r_cmp = matcher.get_apply_res(a, wf1, wf2)
            based_on.add_term(r_cmp.explain_str())
            if not r_cmp.is_false():
                return PosMatchRes(PosMatchRes.dependentFalse, based_on=based_on)

        any_found = False
        based_on.term_start_any()
        for a in self.__apply_if_any:
            r_cmp = matcher.get_apply_res(a, wf1, wf2)
            based_on.add_term(r_cmp.explain_str())
            if not r_cmp.is_false():
                any_found = True

        if not any_found:
            return PosMatchRes(PosMatchRes.dependentFalse, based_on=based_on)

        return self.apply_cb(matcher, wf1, wf2, based_on=based_on)


class PosMatcher(object):
    def __init__(self, pos1_name, pos2_name, default_res=None):
        self.__pos1_name = pos1_name
        self.__pos2_name = pos2_name
        self.__rules = {}
        self.__default_res = default_res

    def get_pos_names(self):
        return (self.__pos1_name, self.__pos2_name)

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
