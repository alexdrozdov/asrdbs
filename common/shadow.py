#!/usr/bin/env python
# -*- #coding: utf8 -*-


import time


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


class ShadowStatsOneMinute(object):
    def __init__(self):
        self.reset()

    def incr_load(self):
        self.__load_count += 1
        self.__hitcount = self.__get_object_count - self.__load_count
        self.__hitrate = float(self.__hitcount) / float(self.__get_object_count)

    def incr_dump(self):
        self.__dump_count += 1

    def incr_get_object(self):
        self.__get_object_count += 1
        self.__hitcount = self.__get_object_count - self.__load_count
        self.__hitrate = float(self.__hitcount) / float(self.__get_object_count)

    def print_stats(self):
        stop_time = time.time()
        delta_time = stop_time - self.__start

        print "\t\ttime: " + str(self.__start) + ", " + str(stop_time) + ", " + str(delta_time)
        print "\t\tloads: " + str(self.__load_count) + " / " + str(float(self.__load_count) / delta_time)
        print "\t\tdumps: " + str(self.__dump_count) + " / " + str(float(self.__dump_count) / delta_time)
        print "\t\tget_object: " + str(self.__get_object_count) + " / " + str(float(self.__get_object_count) / delta_time)
        print "\t\thits: " + str(self.__hitcount) + " / " + str(float(self.__hitcount) / delta_time)
        print "\t\thitrate: " + str(self.__hitrate)

    def reset(self):
        self.__start = time.time()
        self.__load_count = 0
        self.__dump_count = 0
        self.__miss_count = 0
        self.__get_object_count = 0
        self.__hitrate = 0.0

    def can_print_stats(self):
        if time.time() - self.__start > 30:
            return True
        return False


class ShadowStats(object):
    def __init__(self, stat_name, lru_len):
        self.__stat_name = stat_name
        self.__max_entry_count = lru_len
        self.__entry_count = 0
        self.__load_count = 0
        self.__dump_count = 0
        self.__get_object_count = 0
        self.__hitrate = 0.0
        self.__one_min = ShadowStatsOneMinute()

    def incr_load(self):
        self.__load_count += 1
        self.__entry_count += 1
        self.__hitcount = self.__get_object_count - self.__load_count
        self.__hitrate = float(self.__hitcount) / float(self.__get_object_count)
        self.__one_min.incr_load()

    def incr_dump(self):
        self.__dump_count += 1
        self.__entry_count -= 1
        self.__one_min.incr_dump()

    def incr_get_object(self):
        self.__get_object_count += 1
        self.__hitcount = self.__get_object_count - self.__load_count
        self.__hitrate = float(self.__hitcount) / float(self.__get_object_count)
        self.__one_min.incr_get_object()

    def print_stats(self):
        print "Stat name: " + self.__stat_name
        print "\tmax_entry_count: " + str(self.__max_entry_count)
        print "\tentry_count: " + str(self.__entry_count)
        print "\tloads: " + str(self.__load_count)
        print "\tdumps: " + str(self.__dump_count)
        print "\tget_object: " + str(self.__get_object_count)
        print "\thits: " + str(self.__hitcount)
        print "\thitrate: " + str(self.__hitrate)
        print "\tper minute: "
        self.__one_min.print_stats()

    def report_stats(self):
        if self.__one_min.can_print_stats():
            self.print_stats()
            self.__one_min.reset()


class Shadow(object):
    def __init__(self, lru_len=100000, no_reorder=False):
        self.__lru_max_len = lru_len
        self.__no_reorder = no_reorder
        self.__stats = ShadowStats(repr(type(self)), lru_len)
        self.reset()

    def reset(self):
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
            self.__stats.incr_dump()
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
            self.__stats.incr_dump()
            self.dump_object_cb(lru.get_object())
            lru = lru.get_right()
        self.reset()

    def __get_object(self, objid, cache_none=True):
        self.__stats.incr_get_object()
        if objid in self.__cache:
            lru = self.__cache[objid]
            if lru != self.__lru_head and not self.__no_reorder:
                self.__extract_lru(lru)
                self.__push_head(lru)
            return lru.get_object()

        self.__stats.incr_load()
        obj = self.get_object_cb(objid)
        if obj is None and not cache_none:
            return obj

        lru = LruEntry(objid, obj)
        self.__push_head(lru)
        self.__cache[objid] = lru
        self.__obj2objid_dict[lru] = objid
        return lru.get_object()

    def get_object(self, objid, cache_none=True):
        obj = self.__get_object(objid, cache_none)
        self.__stats.report_stats()
        return obj
