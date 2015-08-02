#!/usr/bin/env python
# -*- #coding: utf8 -*-


import base
import gc


class BagClustdbBuilder(base.BagClustdb):
    def __init__(self, dbfilename, rw=True):
        base.BagClustdb.__init__(self, dbfilename, rw=rw)
        self.__create_tables()

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS blobs (blob_id INTEGER PRIMARY KEY, word TEXT, blob TEXT, UNIQUE(word) );',
                    ]

        for c in commands:
            self.execute(c)
        self.commit()

    def __log_progress(self, cnt):
        if cnt % 1000 == 0:
            print "Processed", cnt, "words"
        if cnt % 5000000 == 0:
            print "Flushing primaries..."
            self.flush_bags()
        if cnt % 100000 == 0:
            print "Running gc..."
            gc.collect()

    def add_words(self, words_iter, worddb, window_width=6, max_count=None):
        count = 0
        self.mksync()
        fail_cnt = 0

        ww = WordWindow(window_width)
        while words_iter.has_data() and (max_count is None or count < max_count):
            words = words_iter.get()
            if len(words) < 1:
                print "Failed to get next word", fail_cnt
                fail_cnt += 1
                if fail_cnt > 10:
                    break
                continue
            fail_cnt = 0

            word = words[0]
            word_primaries = worddb.get_word_primaries(word)

            count += 1

            bags = []
            ww.pop_bag_list()

            used_primaries = []
            if word_primaries is None:
                self.__log_progress(count)
                continue

            for pf in word_primaries:
                if pf in used_primaries:
                    continue
                used_primaries.append(pf)

                bag = self.get_bag(pf)
                if bag is None:
                    continue
                bags.append(bag)

            ww.push_bag_list(bags)

            self.__log_progress(count)

        self.flush_bags()
        self.commit()


class WordWindow(object):
    def __init__(self, width=0):
        self.__bags = []
        self.__width = width
        self.__was_filled = False

    def __link_bags(self, b1, b2, distance):
        for bb1 in b1:
            for bb2 in b2:
                bb2.add_neighbor(bb1.get_word(), distance)
                bb1.add_neighbor(bb2.get_word(), distance)

    def pop_bag_list(self):
        if self.__was_filled and len(self.__bags) > self.__width:
            self.__bags = self.__bags[1:]

    def push_bag_list(self, bags):
        for l in range(len(self.__bags)):
            bbags = self.__bags[l]
            if bbags == bags:
                continue
            self.__link_bags(bbags, bags, len(self.__bags) - l)
        self.__bags.append(bags)

        if len(self.__bags) > self.__width:
            self.__was_filled = True
