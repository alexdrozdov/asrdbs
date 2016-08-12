#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3


class Graphdb(object):
    def __init__(self, dbfilename, rw=False):
        self.__init_connection(dbfilename)

    def __init_connection(self, dbfilename):
        self.dbfilename = dbfilename
        self.conn = sqlite3.connect(dbfilename)
        self.cursor = self.conn.cursor()

    def get_alphabet(self):
        self.cursor.execute('SELECT * FROM alphabet ;')
        return self.cursor.fetchall()

    def get_letter_id(self, letter):
        try:
            sql_request = 'SELECT letter_id FROM alphabet WHERE (alphabet.letter=\'{0}\');'.format(letter)
            self.cursor.execute(sql_request)
            return self.cursor.fetchall()[0][0]
        except:
            raise ValueError("Символ {0} не найден в базе".format(letter))

    def get_node_blob(self, node_id):
        sql_request = 'SELECT node_blob FROM node_blobs WHERE (node_blobs.node_id={0});'.format(node_id)
        self.cursor.execute(sql_request)
        res = self.cursor.fetchall()[0][0]
        return eval(res)

    def get_entry_node_blob(self):
        sql_request = 'SELECT node_blob FROM primary_node_blobs;'
        self.cursor.execute(sql_request)
        res = self.cursor.fetchall()[0][0]
        return eval(res)
