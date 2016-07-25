#!/usr/bin/env python
# -*- #coding: utf8 -*-


class IfModified(object):
    def __init__(self, obj, revision_cb):
        self.__obj = obj
        self.__revision_cb = revision_cb
        self.__revision = self.__revision_cb(self.__obj)
        # self.__data = obj.get_form().format('dict')

    def modified(self):
        return self.__revision != self.__revision_cb(self.__obj)

        # revision = self.__revision_cb(self.__obj)
        # if revision != self.__revision:
        #     new_data = self.__obj.get_form().format('dict')
        #     print 'modified: ' + self.__obj.get_form().get_uniq()
        #     for layer, objs in new_data.items():
        #         diff = set(objs.keys()) - set(self.__data[layer].keys()) - set(['word', '__forms'])
        #         diff_vals = ((k, objs[k]) for k in list(diff))
        #         if diff:
        #             try:
        #                 print '    ' + layer + ' / ' + ', '.join((k + ':' + str(v) for k, v in diff_vals))
        #             except:
        #                 print diff
        #                 raise
        #     print ''
        #     return True
        # return False

    def refresh(self):
        self.__revision = self.__revision_cb(self.__obj)

    def get(self):
        return self.__obj

    def __getattr__(self, name):
        return self.__obj.__getattribute__(name)
