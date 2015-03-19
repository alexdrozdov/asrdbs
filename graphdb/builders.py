#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import traceback
import base


class LetterReplaceProbabilities:
    def __init__(self):
        self.originals = {}
        letters = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        for l in letters:
            self.originals[l] = {}

        self.originals[u"а"][u"о"] = 0.2
        self.originals[u"а"][u"у"] = 0.2
        self.originals[u"а"][u"е"] = 0.2
        self.originals[u"а"][u"и"] = 0.2

        self.originals[u"о"][u"а"] = 0.2
        self.originals[u"о"][u"у"] = 0.2
        self.originals[u"о"][u"е"] = 0.2
        self.originals[u"о"][u"и"] = 0.2

        self.originals[u"у"][u"о"] = 0.2
        self.originals[u"у"][u"а"] = 0.2
        self.originals[u"у"][u"е"] = 0.2
        self.originals[u"у"][u"и"] = 0.2

        self.originals[u"е"][u"о"] = 0.2
        self.originals[u"е"][u"у"] = 0.2
        self.originals[u"е"][u"а"] = 0.2
        self.originals[u"е"][u"и"] = 0.2

        self.originals[u"и"][u"о"] = 0.2
        self.originals[u"и"][u"у"] = 0.2
        self.originals[u"и"][u"е"] = 0.2
        self.originals[u"и"][u"а"] = 0.2

        self.originals[u"б"][u"п"] = 0.1
        self.originals[u"п"][u"б"] = 0.1

        self.originals[u"с"][u"з"] = 0.1
        self.originals[u"з"][u"с"] = 0.1

        self.originals[u"в"][u"ф"] = 0.1
        self.originals[u"ф"][u"в"] = 0.1

        self.originals[u"а"][u"а"] = 1.0
        self.originals[u"б"][u"б"] = 1.0
        self.originals[u"в"][u"в"] = 1.0
        self.originals[u"г"][u"г"] = 1.0
        self.originals[u"д"][u"д"] = 1.0
        self.originals[u"е"][u"е"] = 1.0
        self.originals[u"ж"][u"ж"] = 1.0
        self.originals[u"з"][u"з"] = 1.0
        self.originals[u"и"][u"и"] = 1.0
        self.originals[u"й"][u"й"] = 1.0
        self.originals[u"к"][u"к"] = 1.0
        self.originals[u"л"][u"л"] = 1.0
        self.originals[u"м"][u"м"] = 1.0
        self.originals[u"н"][u"н"] = 1.0
        self.originals[u"о"][u"о"] = 1.0
        self.originals[u"п"][u"п"] = 1.0
        self.originals[u"р"][u"р"] = 1.0
        self.originals[u"с"][u"с"] = 1.0
        self.originals[u"т"][u"т"] = 1.0
        self.originals[u"у"][u"у"] = 1.0
        self.originals[u"ф"][u"ф"] = 1.0
        self.originals[u"х"][u"х"] = 1.0
        self.originals[u"ц"][u"ц"] = 1.0
        self.originals[u"ч"][u"ч"] = 1.0
        self.originals[u"ш"][u"ш"] = 1.0
        self.originals[u"щ"][u"щ"] = 1.0
        self.originals[u"ъ"][u"ъ"] = 1.0
        self.originals[u"ы"][u"ы"] = 1.0
        self.originals[u"ь"][u"ь"] = 1.0
        self.originals[u"э"][u"э"] = 1.0
        self.originals[u"ю"][u"ю"] = 1.0
        self.originals[u"я"][u"я"] = 1.0

    def get_repeatable(self):
        return [u"а", u"в", u"е", u"ж", u"з", u"и", u"й", u"л", u"м", u"н", u"о", u"п", u"р", u"с", u"у", u"ф", u"х", u"ш", u"щ", u"ы", u"э", u"ю", u"я"]

    def get_replacements(self, letter):
        try:
            return self.originals[letter]
        except:
            pass
        return None

    def get_originals(self):
        return self.originals.keys()

    def get_probability(self, original, replacement):
        try:
            return self.originals[original][replacement]
        except:
            pass
        return 0.0


class WordSoftlinkBuilder(object):
    def __init__(self, sql_connection, sql_cursor):
        self.conn = sql_connection
        self.cursor = sql_cursor

    def get_letter_id(self, letter):
        try:
            sql_request = u'SELECT letter_id FROM alphabet WHERE (alphabet.letter=\'{0}\');'.format(letter)
            self.cursor.execute(sql_request)
            return self.cursor.fetchall()[0][0]
        except:
            raise ValueError(u"Символ {0} не найден в базе".format(letter))

    def get_hardlinks_by_letter(self, letter):
        letter_id = self.get_letter_id(letter)
        sql_request = 'SELECT from_node, to_node FROM hard_links WHERE (hard_links.letter_id={0});'.format(letter_id)
        self.cursor.execute(sql_request)
        return self.cursor.fetchall()

    def __drop_softlinks_table(self):
        print "Dropping existing softlinks tables..."
        self.cursor.execute('DROP INDEX IF EXISTS from_nodes_idx;')
        self.cursor.execute('DROP TABLE IF EXISTS soft_links;')
        self.conn.commit()
        print "Running vacuum..."
        self.cursor.execute('VACUUM;')
        self.conn.commit()

    def __create_softlinks_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS soft_links (link_id INTEGER PRIMARY KEY, from_node INTEGER, to_node INTEGER, letter_id INTEGER, probability REAL);')

    def __build_index(self):
        self.cursor.execute('CREATE INDEX IF NOT EXISTS from_nodes_idx ON soft_links (from_node) ;')
        self.conn.commit()

    def __build_direct_softlinks(self, max_count=None):
        print "Building direct links..."
        lrp = LetterReplaceProbabilities()
        for l in lrp.get_originals():
            original_nodes = self.get_hardlinks_by_letter(l)
            replacements = lrp.get_replacements(l)
            r_letters = replacements.keys()
            for r in r_letters:
                replacement_letter_id = self.get_letter_id(r)
                sql_params = [(e[0], e[1], replacement_letter_id, lrp.get_probability(l, r)) for e in original_nodes]
                sql_request = 'INSERT INTO soft_links (from_node, to_node, letter_id, probability) VALUES (?, ?, ?, ?);'
                self.cursor.executemany(sql_request, sql_params)
        self.conn.commit()

    def __get_nodes_by_letter(self, letter):
        letter_id = self.get_letter_id(letter)
        sql_request = 'SELECT node_id FROM nodes WHERE (nodes.letter_id={0})'.format(letter_id)
        self.cursor.execute(sql_request)
        return self.cursor.fetchall()

    def __build_self_softlinks(self, max_count=None):
        print "Building self links..."
        lrp = LetterReplaceProbabilities()
        for l in lrp.get_repeatable():
            nodes = self.__get_nodes_by_letter(l)
            replacements = lrp.get_replacements(l)
            r_letters = replacements.keys()
            for r in r_letters:
                replacement_letter_id = self.get_letter_id(r)
                sql_params = [(e[0], e[0], replacement_letter_id, lrp.get_probability(l, r)) for e in nodes]
                sql_request = 'INSERT INTO soft_links (from_node, to_node, letter_id, probability) VALUES (?, ?, ?, ?);'
                self.cursor.executemany(sql_request, sql_params)
        self.conn.commit()

    def build_node_links(self, max_count=None):
        print "Started to build soft links"
        self.__drop_softlinks_table()
        self.__create_softlinks_table()
        self.__build_direct_softlinks(max_count)
        self.__build_self_softlinks(max_count)
        self.__build_index()

    def prepare_insert_request(self, s):
        pass


class WordTrackBuilder(object):
    def __init__(self, sql_connection, sql_cursor):
        self.conn = sql_connection
        self.cursor = sql_cursor

    def build_word_track(self, word):
        try:
            word = word[0]
            letter_list = list(word)
            current_node = "-1"
            for l in letter_list:
                letter_id = self.get_letter_id(l)
                current_node = self.get_letter_node(current_node, letter_id)
            self.set_node_word(current_node, word)
            self.update_hardlink_version(word)
            self.conn.commit()
        except:
            self.conn.rollback()
            print traceback.format_exc()
            print u"Текущее слово -", word
            print u"Транзакция отменена..."

    def get_letter_id(self, letter):
        try:
            sql_request = u'SELECT letter_id FROM alphabet WHERE (alphabet.letter=\'{0}\');'.format(letter)
            self.cursor.execute(sql_request)
            return self.cursor.fetchall()[0][0]
        except:
            raise ValueError(u"Символ {0} не найден в базе".format(letter))

    def get_word_id(self, word):
        sql_request = u'SELECT word_id FROM words WHERE (words.word=\'{0}\');'.format(word)
        # print sql_request
        self.cursor.execute(sql_request)
        return self.cursor.fetchall()[0][0]

    def set_node_word(self, node_id, word):
        word_id = self.get_word_id(word)
        sql_request = 'UPDATE nodes SET word_id={0} WHERE (nodes.node_id={1});'.format(word_id, node_id)
        # print sql_request
        self.cursor.execute(sql_request)

    def update_hardlink_version(self, word):
        sql_request = u'SELECT commit_id FROM words WHERE (words.word=\'{0}\');'.format(word)
        self.cursor.execute(sql_request)
        commit_id = self.cursor.fetchall()[0][0]
        sql_request = u'UPDATE words SET hardlink_version={0} WHERE (words.word=\'{1}\');'.format(commit_id, word)
        self.cursor.execute(sql_request)

    def get_letter_node(self, current_node, letter_id):
        # Сначала пытаемся найти существующую жесткую связь между текущим узлом и следующим узлом по указанной букве
        sql_request = 'SELECT to_node FROM hard_links WHERE (hard_links.from_node={0}) AND (hard_links.letter_id={1});'.format(current_node, letter_id)
        # print sql_request
        self.cursor.execute(sql_request)
        sql_result = self.cursor.fetchall()
        # print sql_result
        if len(sql_result) >= 1:
            # print "node found for", letter_id
            # Узел нашелся - возвращаем его id-шник
            return sql_result[0][0]
        # Узла нет. Создаем узел
        sql_request = 'INSERT INTO nodes (letter_id) VALUES ({0});'.format(letter_id)
        # print sql_request
        self.cursor.execute(sql_request)
        created_node_id = self.cursor.lastrowid
        # Создаем связь к вновь созданному узлу
        sql_request = 'INSERT INTO hard_links (from_node, to_node, letter_id) VALUES ({0}, {1}, {2});'.format(current_node, created_node_id, letter_id)
        # print sql_request
        self.cursor.execute(sql_request)
        return created_node_id


class OptimizedDbBuilder(object):
    def __init__(self, sql_connection, sql_cursor):
        self.conn = sql_connection
        self.cursor = sql_cursor

    def get_word_by_id(self, word_id):
        sql_request = u'SELECT word FROM words WHERE (words.word_id={0});'.format(word_id)
        # print sql_request
        self.cursor.execute(sql_request)
        return self.cursor.fetchall()[0][0]

    def get_node_links(self, node_id):
        by_letter = {}
        sql_request = 'SELECT soft_links.link_id, soft_links.from_node, soft_links.to_node, soft_links.letter_id, alphabet.letter, soft_links.probability FROM soft_links JOIN alphabet USING (letter_id) WHERE (soft_links.from_node={0});'.format(node_id)
        self.cursor.execute(sql_request)
        for l in self.cursor.fetchall():
            link_id = l[0]
            # from_node = l[1]
            to_node = l[2]
            letter_id = l[3]
            letter = l[4]
            probability = l[5]
            if not by_letter.has_key(letter_id):
                by_letter[letter_id] = {"letter_id": letter_id, "letter": letter, "nodes": [(link_id, to_node, probability)]}
            else:
                by_letter[letter_id]["nodes"].append((link_id, to_node, probability))
        return by_letter

    def insert_node_blob(self, node_id, blob):
        blob = blob.replace("'", "''")
        sql_request = 'INSERT INTO node_blobs (node_id, node_blob) VALUES ({0}, \'{1}\')'.format(node_id, blob)
        self.cursor.execute(sql_request)

    def __insert_primary_blob(self, language_id, blob):
        blob = blob.replace("'", "''")
        sql_request = 'INSERT INTO primary_node_blobs (language_id, node_blob) VALUES ({0}, \'{1}\')'.format(language_id, blob)
        self.cursor.execute(sql_request)

    def __drop_optimized_table(self):
        print "Dropping existing optimized tables..."
        self.cursor.execute('DROP INDEX IF EXISTS node_blobs_idx;')
        self.cursor.execute('DROP TABLE IF EXISTS node_blobs;')

        self.cursor.execute('DROP TABLE IF EXISTS primary_node_blobs;')
        self.conn.commit()

        print "Running vacuum..."
        self.cursor.execute('VACUUM;')
        self.conn.commit()

    def __create_optimized_table(self):
        print "Creating new optimized tables..."
        # Создаем таблицу под точки входа в дерево
        self.cursor.execute('CREATE TABLE IF NOT EXISTS primary_node_blobs (language_id INTEGER, node_blob TEXT);')
        # Создаем таблицу под вторичные узлы дерева
        self.cursor.execute('CREATE TABLE IF NOT EXISTS node_blobs (node_id INTEGER, node_blob TEXT);')
        self.conn.commit()

    def __disable_synchronous_mode(self):
        print "Disabling synchronous mode..."
        self.cursor.execute('PRAGMA synchronous=0;')

    def __build_index(self):
        self.cursor.execute('CREATE INDEX IF NOT EXISTS node_blobs_idx ON node_blobs (node_id) ;')
        self.conn.commit()

    def __get_entry_links(self, letter_id):
        sql_request = 'SELECT link_id, to_node, probability FROM soft_links WHERE (soft_links.from_node=-1 AND soft_links.letter_id={0}) ORDER BY soft_links.probability;'.format(letter_id)
        self.cursor.execute(sql_request)
        entries = self.cursor.fetchall()
        return entries

    def __build_primary_entries(self, max_count=None):
        print "Building primary entries..."
        sql_request = 'SELECT letter_id, letter FROM alphabet ORDER BY alphabet.letter_id;'
        self.cursor.execute(sql_request)
        letter_ids = self.cursor.fetchall()
        soft_links = {}
        for l_id in letter_ids:
            letter_id = l_id[0]
            letter = l_id[1]
            entries = self.__get_entry_links(letter_id)
            soft_links[letter_id] = {"letter_id": letter_id,
                                     "letter": letter,
                                     "nodes": [e for e in entries]}
        d = {"node_id": None, "letter_id": None, "letter": None, "word_id": None, "word": None, "soft_links": soft_links}
        blob = str(d)
        self.__insert_primary_blob(0, blob)
        self.conn.commit()

    def __build_secondary_entries(self, max_count=None):
        print "Building secondary entries..."
        if None == max_count:
            sql_request = 'SELECT nodes.node_id, nodes.letter_id, alphabet.letter, nodes.word_id FROM nodes JOIN alphabet USING (letter_id) ;'
        else:
            sql_request = 'SELECT nodes.node_id, nodes.letter_id, alphabet.letter, nodes.word_id FROM nodes JOIN alphabet USING (letter_id) LIMIT {0};'.format(max_count)
        self.cursor.execute(sql_request)
        nodes = self.cursor.fetchall()
        node_count = len(nodes)
        node_cnt = 0
        progress_show_step = int(node_count / 20)
        for n in nodes:
            node_id = n[0]
            letter_id = n[1]
            letter = n[2]
            word_id = n[3]
            word = None
            if None != word_id:
                word = self.get_word_by_id(word_id)
            soft_links = self.get_node_links(node_id)
            d = {"node_id": node_id, "letter_id": letter_id, "letter": letter, "word_id": word_id, "word": word, "soft_links": soft_links}
            blob = str(d)
            self.insert_node_blob(node_id, blob)
            self.conn.commit()
            node_cnt += 1
            if (node_cnt % progress_show_step) == 0:
                print "    {0}% complete".format(node_cnt*100/node_count)

    def build(self, max_count=None):
        print "Started to build optimized table"
        self.__drop_optimized_table()
        self.__create_optimized_table()
        self.__disable_synchronous_mode()
        self.__build_secondary_entries(max_count)
        self.__build_primary_entries(max_count)
        self.__build_index()
        self.conn.commit()


class GraphdbBuilder(base.Graphdb):
    def __init__(self, dbfilename):
        base.Graphdb.__init__(self, dbfilename, rw=True)
        self.__create_tables()

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS words (word_id INTEGER PRIMARY KEY, word TEXT, commit_id INTEGER, hardlink_version INTEGER, UNIQUE (word) );',
                    'CREATE TABLE IF NOT EXISTS alphabet (letter_id INTEGER PRIMARY KEY, letter TEXT, UNIQUE (letter));',
                    'CREATE TABLE IF NOT EXISTS nodes (node_id INTEGER PRIMARY KEY, letter_id INTEGER, word_id INTEGER, commit_id INTEGER);',
                    'CREATE TABLE IF NOT EXISTS hard_links (link_id INTEGER PRIMARY KEY, from_node INTEGER, to_node INTEGER, letter_id INTEGER);',
                    'CREATE TABLE IF NOT EXISTS soft_links (link_id INTEGER PRIMARY KEY, from_node INTEGER, to_node INTEGER, letter_id INTEGER, probability REAL);',
                    'CREATE TABLE IF NOT EXISTS commits (commit_id INTEGER PRIMARY KEY, commit_time TEXT, comment TEXT);']
        for c in commands:
            self.cursor.execute(c)
        self.conn.commit()

    def add_words(self, words_iter, max_count=None, chunk_len=10000, commit_string="Automatic commit name"):
        count = 0
        while words_iter.has_data() and (max_count is None or count < max_count):
            self.cursor.execute('INSERT INTO commits (commit_time, comment)  VALUES (CURRENT_TIMESTAMP, "'+commit_string+'");')
            last_row_id = self.cursor.lastrowid
            words = words_iter.get(chunk_len)
            words_tuple = [(w, last_row_id, 0) for w in words]
            self.cursor.executemany('INSERT OR IGNORE INTO words (word, commit_id, hardlink_version) VALUES (?,?,?);', words_tuple)
            self.conn.commit()
            count += len(words)

    def add_alphabet(self, alphabet):
        alphabet_tuple = [(a,) for a in alphabet]
        self.cursor.executemany('INSERT OR IGNORE INTO alphabet (letter) VALUES (?);', alphabet_tuple)
        self.conn.commit()

    def generate_hardlinks(self, actual_hardlink_version=1, max_count=None):
        self.cursor.execute('PRAGMA synchronous=0;')
        # Выбираем слова, для которых версия жестких ссылок меньше актуальной
        if None == max_count:
            db_request = 'SELECT word FROM words WHERE (words.commit_id > words.hardlink_version);'
        else:
            db_request = 'SELECT word FROM words WHERE (words.commit_id > words.hardlink_version) LIMIT ' + str(max_count) + ';'
        self.cursor.execute(db_request)
        words = self.cursor.fetchall()
        wtb = WordTrackBuilder(self.conn, self.cursor)
        for w in words:
            wtb.build_word_track(w)

    def generate_softlinks(self):
        wsb = WordSoftlinkBuilder(self.conn, self.cursor)
        wsb.build_node_links()

    def generate_optimized(self, max_count=None):
        odb = OptimizedDbBuilder(self.conn, self.cursor)
        odb.build(max_count)


def common_startup():
    if os.path.exists("./graphdb.db"):
        return GraphdbBuilder('./graphdb.db')
    wdd = GraphdbBuilder('./graphdb.db')
    # wdd.add_alphabet(u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    # load_odict(wdd, "./o_dict.pickle")
    return wdd

if __name__ == '__main__':
    wdd = common_startup()
    # wdd.generate_hardlinks(1)
    # wdd.generate_softlinks()
    # wdd.generate_optimized()
