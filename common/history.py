#!/usr/bin/env python
# -*- #coding: utf8 -*-


import output


class History(object):
    def __init__(self, subpath=None):
        self.__subpath = subpath if subpath is not None else 'hist'
        self.__obj2inst = {}
        self.__subobj2inst = {}
        self.__filecount = 0

    def _register_suboject_inst(self, inst, objinfo):
        subobj = objinfo['subobj']
        is_uniq = objinfo['uniq']
        is_shared = objinfo['shared']
        if self.__subobj2inst.has_key(subobj):
            hist_subobjinfo = self.__subobj2inst[subobj]
            assert len(hist_subobjinfo)
            if is_uniq:
                assert len(hist_subobjinfo) == 1
                assert hist_subobjinfo[0]['inst'] == inst
                assert hist_subobjinfo[0]['uniq'] == is_uniq and hist_subobjinfo[0]['shared'] == is_shared
            else:
                for inst_objinfo in hist_subobjinfo:
                    if inst_objinfo['inst'] == inst:
                        return
                hist_subobjinfo.append({'inst': inst, 'uniq': is_uniq, 'shared': is_shared})
            return
        self.__subobj2inst[subobj] = [{'inst': inst, 'uniq': is_uniq, 'shared': is_shared}, ]

    def register_object(self, obj, label=None, is_clone_of=None, assert_not_registered=True):
        if self.__obj2inst.has_key(obj):
            assert not assert_not_registered
            return
        filename = output.output.get_output_file(self.__subpath, 'hist-{0}.txt'.format(self.__filecount))
        self.__filecount += 1
        hi = HistoryInst(self, obj, label, filename)
        if is_clone_of:
            assert self.__obj2inst.has_key(is_clone_of)
            hi.copy_history(self.__obj2inst[is_clone_of])
        self.__obj2inst[obj] = hi

    def register_subobject(self, obj, subobj, label=None, is_uniq=True, is_shared=False):
        assert self.__obj2inst.has_key(obj)
        hi = self.__obj2inst[obj]
        hi.add_subobject(subobj, label=label, is_uniq=is_uniq, is_shared=is_shared)

    def log(self, obj, log_string):
        if self.__obj2inst.has_key(obj):
            self.__obj2inst[obj].log(obj, log_string)
        elif self.__subobj2inst.has_key(obj):
            for inst in self.__subobj2inst[obj]:
                inst['inst'].log(obj, log_string)
        else:
            raise KeyError('{0} is not registered in history logger'.format(str(obj)))


class HistoryInst(object):
    def __init__(self, history, obj, label, filename):
        self.__history = history
        self.__obj = obj
        self.__filename = filename
        self.__label = label if label is not None else str(obj)
        self.__subojects = {}
        self.__fd = None
        self.__lines = []

    def add_subobject(self, subobj, label=None, is_uniq=True, is_shared=False):
        assert is_uniq != is_shared
        if self.__subojects.has_key(subobj):
            objinfo = self.__subojects[subobj]
            assert objinfo['uniq'] == is_uniq and objinfo['shared'] == is_shared
        else:
            objinfo = {'subobj': subobj, 'uniq': is_uniq, 'shared': is_shared, 'label': label if label is not None else str(subobj)}
            self.__subojects[subobj] = objinfo
            self.__history._register_suboject_inst(self, objinfo)

    def __add_line(self, log_str):
        self.__fd.write(log_str.encode('utf8'))
        self.__lines.append(log_str)
        self.__fd.flush()

    def copy_history(self, other_hi):
        if self.__fd is None:
            self.__fd = open(self.__filename, 'w')
        self.__add_line('>>>> copied from HistInst {0}\r\n'.format(other_hi.__label))
        for ls in other_hi.__lines:
            self.__add_line(ls)
        self.__add_line('<<<< copied from HistInst {0}\r\n'.format(other_hi.__label))

    def log(self, obj, log_string):
        if self.__fd is None:
            self.__fd = open(self.__filename, 'w')
        if self.__subojects.has_key(obj):
            subobj_label = self.__subojects[obj]['label']
        else:
            subobj_label = 'base'
        log_str = u'{0} - {1}: {2}\r\n'.format(self.__label, subobj_label, log_string)
        self.__add_line(log_str)


class H(object):
    history = None

    def __new__(self, subpath=None):
        if self.history is None:
            self.history = History(subpath)
        return self.history


def register_object(obj, label=None, is_clone_of=None, assert_not_registered=True):
    h = H()
    h.register_object(obj, label, is_clone_of, assert_not_registered)


def register_subobject(obj, subobj, label=None, is_uniq=True, is_shared=False):
    h = H()
    h.register_subobject(obj, subobj, label, is_uniq, is_shared)


def log(obj, log_string):
    h = H()
    h.log(obj, log_string)


def en(obj=None):
    return False
