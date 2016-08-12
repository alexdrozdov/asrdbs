#!/usr/bin/env python
# -*- #coding: utf8 -*-

import traceback
from . import base


class LibrudbBuilder(base.Librudb):
    def __init__(self, dbfilename, rw=False):
        base.Librudb.__init__(self, dbfilename, rw=True)
        self.__create_tables()
        self.mksync()

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS lib'
                    '(text_id INTEGER PRIMARY KEY, path TEXT, md5 TEXT, content TEXT,'
                    'UNIQUE(path), UNIQUE(md5) );',
                    ]

        for c in commands:
            self.execute(c)
        self.commit()

    def set_file_count(self, count):
        self.all_file_count = count

    def __add_file(self, filename):
        path = filename.lower()
        print("\tAdding file " + filename + "...")
        if self.path_exists(path):
            print("\t\tPath exists, ignoring...")
            return
        try:
            with open(filename) as f:
                content = f.read().decode("utf8")
            md5 = self.md5(content)
            if self.md5_exists(md5):
                print("\t\tMD5 exists, ignoring...")
                return
            self.execute('INSERT INTO lib (path, md5, content) VALUES(?,?,?);', (path, md5, content))
        except:
            print(traceback.format_exc())

    def add_files(self, file_iter, max_count=None):
        count = 0
        self.mksync()

        while file_iter.has_data() and (max_count is None or count < max_count):
            filename = file_iter.get()
            self.__add_file(filename)
            count += 1
            if count % 1000 == 0:
                print("Inserted", count, "files")
        self.commit()
