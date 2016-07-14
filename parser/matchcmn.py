#!/usr/bin/env python
# -*- #coding: utf8 -*-


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

    def __str__(self):
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

    def __nonzero__(self):
        return self.is_true()

    def __bool__(self):
        return self.is_true()


class PosMatchRes(object):
    def __init__(self, details):
        self.__details = details

    def is_false(self):
        return self.value() < MatchBool.invariantBool

    def is_true(self):
        return self.value() > MatchBool.invariantBool

    def value(self):
        return self.__details['res']

    def reliability(self):
        return self.__details['reliability']

    def get_rule_name(self):
        return self.__details['rule']

    def to_dict(self):
        return self.__details

    def __str__(self):
        return str(self.__details)

    def __nonzero__(self):
        return self.is_true()


class independentFalse(PosMatchRes):
    def __init__(self, rule_name='independentFalse'):
        super(independentFalse, self).__init__(
            {'rule': rule_name,
             'res': MatchBool.independentFalse,
             'reliability': 1.0
             }
        )


class dependentFalse(PosMatchRes):
    def __init__(self, rule_name='dependentFalse'):
        super(dependentFalse, self).__init__(
            {'rule': rule_name,
             'res': MatchBool.dependentFalse,
             'reliability': 1.0
             }
        )


class defaultFalse(PosMatchRes):
    def __init__(self, rule_name='defaultFalse'):
        super(defaultFalse, self).__init__(
            {'rule': rule_name,
             'res': MatchBool.defaultFalse,
             'reliability': 1.0
             }
        )


class invariantBool(PosMatchRes):
    def __init__(self, rule_name='invariantBool'):
        super(invariantBool, self).__init__(
            {'rule': rule_name,
             'res': MatchBool.invariantBool,
             'reliability': 1.0
             }
        )


class defaultTrue(PosMatchRes):
    def __init__(self, rule_name='defaultTrue'):
        super(defaultTrue, self).__init__(
            {'rule': rule_name,
             'res': MatchBool.defaultTrue,
             'reliability': 1.0
             }
        )


class possibleTrue(PosMatchRes):
    def __init__(self, rule_name='possibleTrue'):
        super(possibleTrue, self).__init__(
            {'rule': rule_name,
             'res': MatchBool.possibleTrue,
             'reliability': 1.0
             }
        )


class reliableTrue(PosMatchRes):
    def __init__(self, rule_name='reliableTrue'):
        super(reliableTrue, self).__init__(
            {'rule': rule_name,
             'res': MatchBool.reliableTrue,
             'reliability': 1.0
             }
        )


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

    def apply(self, res_dict, wf1, wf2):
        details = {"rule": self.__name}

        reliability = 1.0
        if self.__apply_if_all:
            __and = []
            for a in self.__apply_if_all:
                r_cmp = res_dict[a]
                __and.append(r_cmp.to_dict())
                reliability *= r_cmp.reliability()
                if r_cmp.is_false():
                    details['all'] = __and
                    details['res'] = dependentFalse().value()
                    details['reliability'] = r_cmp.reliability()
                    return PosMatchRes(details=details), self.__false_is_final
            details['all'] = __and

        if self.__apply_if_none:
            __none = []
            for a in self.__apply_if_none:
                r_cmp = res_dict[a]
                __none.append(r_cmp.to_dict())
                reliability *= r_cmp.reliability()
                if not r_cmp.is_false():
                    details['none'] = __none
                    details['res'] = dependentFalse().value()
                    details['reliability'] = r_cmp.reliability()
                    return PosMatchRes(details=details), self.__false_is_final
            details['none'] = __none

        if self.__apply_if_any:
            __any = []
            for a in self.__apply_if_any:
                r_cmp = res_dict[a]
                __any.append(r_cmp.to_dict())
                reliability *= r_cmp.reliability()
                if not r_cmp.is_false():
                    details['any'] = __any
                    break
            else:
                details['any'] = __any
                details['res'] = dependentFalse().value()
                details['reliability'] = r_cmp.reliability()
                return PosMatchRes(details=details), self.__false_is_final

        r_cmp = self.apply_cb(res_dict, wf1, wf2)
        reliability *= r_cmp.reliability()
        details['apply_cb'] = r_cmp.to_dict()
        details['res'] = r_cmp.value()
        details['reliability'] = reliability
        res = PosMatchRes(details=details)
        return res, self.res_is_final(res)


class PosMatcher(object):
    def __init__(self, pos1_name, pos2_name, default_res=None):
        self.__pos1_name = pos1_name
        self.__pos2_name = pos2_name
        self.__name = self.__pos1_name + "_" + self.__pos2_name
        self.__rules = []
        self.__default_res = default_res

    def get_pos_names(self):
        return (self.__pos1_name, self.__pos2_name)

    def get_name(self):
        return self.__name

    def add_rule(self, rule):
        self.__rules.append(rule)

    def match(self, wf1, wf2):
        res_dict = {}
        for rule in self.__rules:
            res, final = rule.apply(res_dict, wf1, wf2)
            res_dict[rule.get_name()] = res
            if final:
                return res
        return self.__default_res
