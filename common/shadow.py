#!/usr/bin/env python
# -*- #coding: utf8 -*-


class LruEntry(object):
    def __init__(self, objid, obj, left=None, right=None):
        self.__objid = objid
        self.__obj = obj
        self.__left = left
        self.__right = right

    def self_extract(self):
        if self.__left is not None:
            self.__left.__right = self.__right
        if self.__right is not None:
            self.__right.__left = self.__left
        self.__left = None
        self.__right = None

    def self_insert_righter_than(self, left_entry):
        self.__left = left_entry
        if left_entry.__right is not None:
            self.__right = left_entry.__right
            self.__right.__left = self
        left_entry.__right = self

    def get_object(self):
        return self.__obj

    def get_objid(self):
        return self.__objid

    def get_left(self):
        return self.__left

    def get_right(self):
        return self.__right


class Shadow(object):
    def __init__(self, lru_len=1000):
        self.__lru_max_len = lru_len
        self.__cache = {}
        self.__lru_head = None
        self.__lru_tail = None
        self.__lru_len = 0
        self.__obj2objid_dict = {}

    def print_self(self):
        print self.__lru_tail, type(self.__lru_tail)
        print self.__lru_head, type(self.__lru_head)

    def __pop_tail(self):
        if self.__lru_tail is None or self.__lru_len == 0:
            return
        rm = self.__lru_tail
        self.__lru_tail = self.__lru_tail.get_right()
        rm.self_extract()
        if self.__lru_tail is None:
            self.__lru_head = None
        self.__lru_len -= 1
        return rm

    def __pop_head(self):
        if self.__lru_head is None or self.__lru_len == 0:
            return
        rm = self.__lru_head
        self.__lru_head = self.__lru_head.get_left()
        rm.self_extract()
        if self.__lru_head is None:
            self.__lru_tail = None
        self.__lru_len -= 1

    def __del_from_cache(self, lru_entry):
        objid = self.__obj2objid_dict.pop(lru_entry)
        self.__cache.pop(objid)

    def __extract_lru(self, lru_entry):
        self.__del_from_cache(lru_entry)
        if self.__lru_tail == lru_entry:
            self.__pop_tail()
            return
        if self.__lru_head == lru_entry:
            self.__pop_head()
            return
        lru_entry.self_extract()
        self.__lru_len -= 1

    def __push_head(self, lru_entry):
        if self.__lru_len >= self.__lru_max_len:
            rm = self.__pop_tail()
            self.dump_object_cb(rm.get_object())
            self.__del_from_cache(rm)
        if self.__lru_head is None:
            self.__lru_head = lru_entry
            self.__lru_tail = lru_entry
        else:
            lru_entry.self_insert_righter_than(self.__lru_head)
            self.__lru_head = lru_entry
        self.__cache[lru_entry.get_objid()] = lru_entry
        self.__obj2objid_dict[lru_entry] = lru_entry.get_objid()
        self.__lru_len += 1

    def flush(self):
        lru = self.__lru_tail
        while lru is not None:
            self.dump_object_cb(lru.get_object())
            lru = lru.get_right()

    def get_object(self, objid, cache_none=True):
        if self.__cache.has_key(objid):
            lru = self.__cache[objid]
            if lru != self.__lru_head:
                self.__extract_lru(lru)
                self.__push_head(lru)
            return lru.get_object()

        obj = self.get_object_cb(objid)
        if obj is None and not cache_none:
            return obj

        lru = LruEntry(objid, obj)
        self.__push_head(lru)
        self.__cache[objid] = lru
        self.__obj2objid_dict[lru] = objid
        return lru.get_object()
