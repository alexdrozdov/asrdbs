#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import base
import common.shadow


class Graphdb(base.Graphdb, common.shadow.Shadow):
    def __init__(self, dbfilename, lru_len=1000):
        base.Graphdb.__init__(dbfilename, rw=False)
        common.shadow.Shadow.__init__(self, lru_len=lru_len)
        self.__entry_blob = NodeBlob(self, None)

    def get_raw_node_blob(self, node_id):
        return base.Graphdb.get_node_blob(self, node_id)

    def get_raw_entry_node_blob(self):
        return base.Graphdb.get_entry_node_blob(self)

    def get_entry_node_blob(self):
        return self.__entry_blob

    def get_node_blob(self, node_id):
        return self.get_object(node_id)

    def get_object_cb(self, objid):
        node_id = objid
        return NodeBlob(self, node_id)

    def dump_object_cb(self, obj):
        pass


class NodeBlob(object):
    def __init__(self, worddb, node_id=None):
        self.__worddb = worddb
        self.__node_id = node_id
        if self.__node_id is None:
            self.__blob = self.__worddb.get_raw_entry_node_blob()
        else:
            self.__blob = self.__worddb.get_raw_node_blob(node_id)
        self.__load_alphabet()

    def __load_alphabet(self):
        alphabet = self.__worddb.get_alphabet()
        self.a2i_dict = {}
        self.i2a_dict = {}
        for a, i in alphabet:
            self.a2i_dict[a] = i
            self.i2a_dict[i] = a

    def has_subletter(self, letter):
        letter_id = self.a2i_dict[letter]
        return self.__blob['soft_links'].has_key(letter_id)

    def get_subletter_link_ids(self, letter):
        letter_id = self.a2i_dict[letter]
        link_ids = [x[0] for x in self.__blob['soft_links'][letter_id]['nodes']]
        return link_ids

    def get_subletter_node_ids(self, letter):
        letter_id = self.a2i_dict[letter]
        node_ids = [x[1] for x in self.__blob['soft_links'][letter_id]['nodes']]
        return node_ids

    def get_subletter_nodes(self, letter, need_probability=False):
        letter_id = self.a2i_dict[letter]
        if not need_probability:
            nodes = [NodeBlob(self.__worddb, x[1]) for x in self.__blob['soft_links'][letter_id]['nodes']]
        else:
            nodes = [(NodeBlob(self.__worddb, x[1]), x[2]) for x in self.__blob['soft_links'][letter_id]['nodes']]
        return nodes

    def get_letter(self):
        return self.__blob['letter']

    def get_node_id(self):
        return self.__node_id

    def get_word(self):
        return self.__blob['word']

    def get_word_id(self):
        return self.__blob['word_id']


class WordTreeItem(object):
    def __init__(self, worddb, node_id):
        self.node_id = node_id
        self.worddb = worddb
        sql_request = 'SELECT letter_id FROM nodes WHERE (nodes.node_id={0}) ;'.format(node_id)
        self.worddb.cursor.execute(sql_request)
        fa = self.worddb.cursor.fetchall()
        if len(fa) < 1:
            self.letter = u''
        else:
            letter_id = int(fa[0][0])
            sql_request = 'SELECT letter FROM alphabet WHERE (alphabet.letter_id={0}) ;'.format(letter_id)
            self.worddb.cursor.execute(sql_request)
            self.letter = self.worddb.cursor.fetchall()[0][0]

        self.word = None
        try:
            sql_request = 'SELECT word_id FROM nodes WHERE (nodes.node_id={0}) ;'.format(node_id)
            self.worddb.cursor.execute(sql_request)
            fa = self.worddb.cursor.fetchall()
            if len(fa) >= 1:
                word_id = fa[0][0]
                # print "word_id", word_id
                sql_request = 'SELECT word FROM words WHERE (words.word_id={0}) ;'.format(word_id)
                self.worddb.cursor.execute(sql_request)
                self.word = self.worddb.cursor.fetchall()[0][0]
                # print "node word", self.word
        except:
            pass

    def has_subletter(self, letter):
        letter_id = self.worddb.get_letter_id(letter)
        sql_request = 'SELECT COUNT(link_id) FROM soft_links WHERE (soft_links.from_node={0} AND soft_links.letter_id={1}) ;'.format(self.node_id, letter_id)
        self.worddb.cursor.execute(sql_request)
        links_count = int(self.worddb.cursor.fetchall()[0][0])
        # print "links_count", letter, links_count
        return links_count > 0

    def get_subletter_links(self, letter):
        letter_id = self.worddb.get_letter_id(letter)
        sql_request = 'SELECT link_id FROM soft_links WHERE (soft_links.from_node={0} AND soft_links.letter_id={1}) ;'.format(self.node_id, letter_id)
        self.worddb.cursor.execute(sql_request)
        links = [x[0] for x in self.worddb.cursor.fetchall()]
        # print "links for", letter, links
        return links

    def get_probability(self, cross_item_link):
        sql_request = 'SELECT probability FROM soft_links WHERE (soft_links.link_id={0}) ;'.format(cross_item_link)
        self.worddb.cursor.execute(sql_request)
        probability = float(self.worddb.cursor.fetchall()[0][0])
        return probability

    def get_child(self, cross_item_link):
        sql_request = 'SELECT to_node FROM soft_links WHERE (soft_links.link_id={0}) ;'.format(cross_item_link)
        self.worddb.cursor.execute(sql_request)
        node = int(self.worddb.cursor.fetchall()[0][0])
        # print "link to node", cross_item_link, node
        node = WordTreeItem(self.worddb, node)
        return node

    def get_letter(self):
        return self.letter

    def get_node_id(self):
        return self.node_id


class WordTree(WordTreeItem):
    def __init__(self, worddb):
        WordTreeItem.__init__(self, worddb, -1)


def common_startup():
    if os.path.exists("./graphdb.db"):
        return Graphdb('./graphdb.db')
    wdd = Graphdb('./graphdb.db')
    return wdd

if __name__ == '__main__':
    wdd = common_startup()
