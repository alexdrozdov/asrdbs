#!/usr/bin/env python
# -*- #coding: utf8 -*-

import sqlite3
import hashlib


class LibruText(object):
    def __init__(self, text_id, path, md5, content):
        self.__text_id = text_id
        self.__path = path
        self.__md5 = md5
        self.__content = content

    def get_textid(self):
        return self.__text_id

    def get_path(self):
        return self.__path

    def get_md5(self):
        return self.__md5

    def get_content(self):
        return self.__content


class Librudb(object):
    def __init__(self, dbfilename, rw=False):
        self.__init_connection(dbfilename)

    def __init_connection(self, dbfilename):
        self.dbfilename = dbfilename
        self.conn = sqlite3.connect(dbfilename)
        self.cursor = self.conn.cursor()
        self.cursor.execute('PRAGMA synchronous=0;')

    def md5(self, content):
        m = hashlib.new('md5')
        m.update(content.encode('utf8'))
        return m.hexdigest().lower()

    def path_exists(self, path):
        self.cursor.execute('SELECT path FROM lib WHERE (lib.path=?);', (path,))
        return len(self.cursor.fetchall()) > 0

    def md5_exists(self, md5):
        query = 'SELECT md5 FROM lib WHERE (lib.md5=\'' + md5 + '\');'
        self.cursor.execute(query)
        return len(self.cursor.fetchall()) > 0

    def get_text_by_id(self, text_id):
        self.cursor.execute('SELECT text_id, path, md5, content FROM lib WHERE (lib.text_id=?);', (text_id,))
        r = self.cursor.fetchall()
        if len(r) == 0:
            return None

        text_id, path, md5, content = r[0]

        return LibruText(text_id, path, md5, content)

    def get_text_by_md5(self, md5):
        self.cursor.execute('SELECT text_id, path, md5, content FROM lib WHERE (lib.md5=?);', (md5,))
        r = self.cursor.fetchall()
        if len(r) == 0:
            return None

        text_id, path, md5, content = r[0]

        return LibruText(text_id, path, md5, content)

    def get_text_by_path(self, path):
        self.cursor.execute('SELECT text_id, path, md5, content FROM lib WHERE (lib.path=?);', (path,))
        r = self.cursor.fetchall()
        if len(r) == 0:
            return None

        text_id, path, md5, content = r[0]

        return LibruText(text_id, path, md5, content)

    def get_author_texts(self, author):
        return None
