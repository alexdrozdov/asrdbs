#!/usr/bin/env python
# -*- #coding: utf8 -*-


import json
import base
import common.shadow
import traceback
import gc

class Forms:
    terms = {
        "parts_of_speech": {
            "noun": u"сущ",
            "adjective": u"прл",
            "verb": u"гл",
            "participal": [u"прч", u"дееп"],
            "union": [u"союз", u"межд", u"предик"],
            "particle": u"част",
            "numeral": u"числ",
            "pronoun": u"мест",
            "adverb": u"нар",
            "preposition": u"предл",
            "inp": u"ввод",
        },

        "count": {
            "singilar": u"ед",
            "plural": u"мн"
        },

        "gender": {
            "male": u"муж",
            "female": u"жен",
            "neuter": u"ср"
        },

        "animation": {
            "animated": u"одуш",
            "inanimated": u"неод"
        },

        "case": {
            "nominative": u"им",
            "genitive": u"род",
            "dative": u"дат",
            "accusative": u"вин",
            "ablative": u"тв",
            "prepositional": u"пр"
        },

        "verb_form": {
            "perfect": u"несов",
            "imperfect": u"сов"
        },

        "time": {
            "infinitive": u"инф",
            "past": u"прош",
            "present": u"наст",
            "future": u"буд"
        }
    }

    def __init__(self):
        self.transforms = {}
        self.unknown = {}
        for term_name, term_values in Forms.terms.items():
            for term_value, term_code in term_values.items():
                if isinstance(term_code, list):
                    for c in term_code:
                        self.transforms[c] = {"term": term_name, "value": term_value, "code": c}
                else:
                    self.transforms[term_code] = {"term": term_name, "value": term_value, "code": term_code}

    def generate_classes(self):
        pass

    def list_to_terms(self, l):
        res = {}
        for i in l:
            i = i.decode("utf8")
            try:
                term = self.transforms[i]
                res[term["term"]] = term["value"]
            except:
                if self.unknown.has_key(i):
                    self.unknown[i] += 1
                else:
                    self.unknown[i] = 1
        return res

    def print_unknowns(self):
        for k, v in self.unknown.items():
            print k.encode("utf8"), v


class MorfWordGroup(object):
    def __init__(self):
        self.primary = None
        self.forms = []

    def add_entry(self, word, info):
        if None == self.primary:
            self.primary = (word, info)
            return
        self.forms.append((word, info))

    def len(self):
        if None == self.primary:
            return 0
        return 1+len(self.forms)


class WordFormsShadow(common.db.Db, common.shadow.Shadow):
    def __init__(self, reuse_db, lru_len=100000):
        common.shadow.Shadow.__init__(self, lru_len=lru_len)
        common.db.Db.__init__(self, reuse_db=reuse_db)

    def get_object_cb(self, objid):
        res = []
        word_id = objid
        self.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.root=?);', (word_id,))
        for word_id, word, root, class_id in self.fetchall():
            res.append({"word": word, "class_id": class_id})
        return res

    def dump_object_cb(self, obj):
        pass


class WordShadow(common.db.Db, common.shadow.Shadow):
    def __init__(self, reuse_db, lru_len=100000):
        common.shadow.Shadow.__init__(self, lru_len=lru_len)
        common.db.Db.__init__(self, reuse_db=reuse_db)

    def get_object_cb(self, objid):
        self.execute('SELECT word_id, word, root, class_id FROM words WHERE (words.word_id=?);', (objid, ))
        return self.fetchall()[0]

    def dump_object_cb(self, obj):
        pass


class PrimaryFormShadow(common.db.Db, common.shadow.Shadow):
    def __init__(self, reuse_db, lru_len=100000):
        common.shadow.Shadow.__init__(self, lru_len=lru_len, no_reorder=True)
        common.db.Db.__init__(self, reuse_db=reuse_db)

    def get_object_cb(self, objid):
        self.execute('SELECT prim_id, word, pos, total_count, blob FROM primaries WHERE (primaries.word=?);', (objid, ))
        r = self.fetchall()
        if len(r) == 0:
            return None
        res = []
        for rr in r:
            prim_id = rr[0]
            word = rr[1]
            pos = rr[2]
            total_count = rr[3]
            jblob = rr[4]
            pf = PrimaryForm(prim_id, word, pos, total_count, json.loads(jblob))
            res.append(pf)
        return res

    def dump_object_cb(self, obj):
        if obj is None:
            return
        for pf in obj:
            self.execute('UPDATE primaries SET total_count=?, blob=? WHERE (primaries.prim_id=?);', (pf.get_total_use_count(), pf.get_jblob(), pf.get_primary_id()))


class PrimaryForm(object):
    def __init__(self, prim_id, word, pos, total_count, info):
        self.__prim_id = prim_id
        self.__word = word
        self.__pos = pos
        self.__total_count = total_count if total_count is not None else 0
        self.__info = info

    def get_word(self):
        return self.__word

    def get_primary_id(self):
        return self.__prim_id

    def get_pos(self):
        return self.__pos

    def get_total_use_count(self):
        return self.__total_count

    def get_jblob(self):
        return json.dumps(self.__info, ensure_ascii=False)

    def increase_total_usage(self, val=1):
        self.__total_count += val
        try:
            cur_val = self.__info['total_use_count']
        except:
            cur_val = 0
        cur_val += val
        self.__info['total_use_count'] = cur_val

    def increase_form_usage(self, form, val=1):
        for wf in self.__info['forms']:
            if wf[0] != form:
                continue
            try:
                cur_val = wf[1]['use_count']
            except:
                cur_val = 0
            cur_val += val
            wf[1]['use_count'] = cur_val

        if self.__info['word'] == form:
            try:
                cur_val = self.__info['use_count']
            except:
                cur_val = 0
            cur_val += val
            self.__info['use_count'] = cur_val


class WordIdsShadow(common.db.Db, common.shadow.Shadow):
    def __init__(self, reuse_db, lru_len=100000):
        common.shadow.Shadow.__init__(self, lru_len=lru_len)
        common.db.Db.__init__(self, reuse_db=reuse_db)

    def get_object_cb(self, objid):
        word = objid
        ids = self.execute('SELECT word_ids FROM wordlist WHERE (wordlist.word=?);', (word,)).fetchall()
        if len(ids) == 0:
            return None
        ids = eval(ids[0][0])
        return ids

    def dump_object_cb(self, obj):
        pass


class WorddbBuilder(base.Worddb):
    def __init__(self, dbfilename, rw=True):
        base.Worddb.__init__(self, dbfilename, rw=rw, no_classes=True)
        self.__create_tables()
        self.__load_classes()
        self.__w_shadow = WordShadow(reuse_db=self)
        self.__wids_shadow = WordIdsShadow(reuse_db=self)
        self.__wf_shadow = WordFormsShadow(reuse_db=self)
        self.__pf_shadow = PrimaryFormShadow(reuse_db=self, lru_len=1000000)
        self.ft = Forms()

    def __load_classes(self):
        self.classes = WordClassesBuilder(reuse_db=self)

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS words (word_id INTEGER PRIMARY KEY, word TEXT, root INTEGER, commit_id INTEGER, class_id INTEGER, UNIQUE(word,class_id) );',
                    'CREATE TABLE IF NOT EXISTS primaries (prim_id INTEGER PRIMARY KEY, word TEXT, pos TEXT, total_count INTEGER, blob TEXT);',
                    'CREATE TABLE IF NOT EXISTS commits (commit_id INTEGER PRIMARY KEY, commit_time TEXT, comment TEXT);',
                    'CREATE TABLE IF NOT EXISTS alphabet (letter_id INTEGER PRIMARY KEY, letter TEXT, UNIQUE (letter));',
                    'CREATE TABLE IF NOT EXISTS wordlist (uword_id INTEGER PRIMARY KEY, word TEXT, word_ids TEXT, cnt INTEGER, UNIQUE(word));',
                    ]

        for c in commands:
            self.execute(c)
        self.commit()

    def line_to_form(self, line):
        line_terms = line.split('\t')
        word = line_terms[0]
        line_terms = line_terms[1].split(' ')
        info = self.ft.list_to_terms(line_terms)

        return (word.decode("utf8"), info)

    def add_alphabet(self, alphabet):
        alphabet_tuple = [(a,) for a in alphabet]
        self.executemany('INSERT OR IGNORE INTO alphabet (letter) VALUES (?);', alphabet_tuple)
        self.commit()

    def add_word_group(self, word_group, commit_string="Automatic commit name"):
        self.execute('INSERT INTO commits (commit_time, comment)  VALUES (CURRENT_TIMESTAMP, "'+commit_string+'");')
        commit_id = self.get_lastrowid()

        cid = self.classes.get_class_id(repr(word_group.primary[1]))
        self.execute('INSERT OR IGNORE INTO words (word, root, commit_id, class_id) VALUES (?,?,?,?)',
                     (word_group.primary[0], -1, commit_id, cid))

        word_id = self.get_lastrowid()

        words_tuple = [(w, word_id, commit_id, self.classes.get_class_id(repr(i))) for w, i in word_group.forms]
        self.executemany('INSERT OR IGNORE INTO words (word, root, commit_id, class_id) VALUES (?,?,?,?);', words_tuple)
        self.commit()

    def add_primary(self, word_group):
        word = word_group.primary[0]
        try:
            pos = word_group.primary[1]['parts_of_speech']
        except:
            print traceback.format_exc()
            print word_group.primary[0]
            return
        info = {'word': word}
        info['pos_info'] = word_group.primary[1]
        info['forms'] = word_group.forms
        info = json.dumps(info, ensure_ascii=False)
        self.execute('INSERT OR IGNORE INTO primaries (word, pos, blob) VALUES (?,?,?)',
                     (word, pos, info))
        self.commit()

    def __build_word_index(self):
        print "Building words index..."
        self.execute('CREATE INDEX IF NOT EXISTS words_idx ON words (word) ;')
        self.execute('CREATE INDEX IF NOT EXISTS words_root_idx ON words (root) ;')
        self.execute('CREATE INDEX IF NOT EXISTS words_class_idx ON words (class_id) ;')
        self.execute('CREATE INDEX IF NOT EXISTS primaries_idx ON primaries (word) ;')
        self.commit()

    def __drop_word_index(self):
        print "Dropping words index..."
        self.execute('DROP INDEX IF EXISTS words_idx;')
        self.execute('DROP INDEX IF EXISTS words_root_idx;')
        self.execute('DROP INDEX IF EXISTS words_class_idx;')
        self.execute('DROP INDEX IF EXISTS primaries_idx;')

    def __build_wordlist_index(self):
        print "Building wordlist index..."
        self.execute('CREATE INDEX IF NOT EXISTS wordslist_idx ON wordlist (word) ;')
        self.commit()

    def __recreate_wordlist(self):
        print "Dropping wordlist index..."
        self.execute('DROP INDEX IF EXISTS wordlist_idx;')
        self.execute('DROP TABLE IF EXISTS wordlist;')
        self.execute('CREATE TABLE IF NOT EXISTS wordlist (uword_id INTEGER PRIMARY KEY, word TEXT, word_ids TEXT, cnt INTEGER, UNIQUE(word));')

    def build_wordlist(self, max_count=None):
        print "Building full word list..."
        self.__recreate_wordlist()

        print "Selecting complete word list..."
        query = 'SELECT DISTINCT word FROM words;'
        self.execute(query)
        words = self.fetchall()

        word_count = len(words)
        print_step = word_count / 20
        word_cnt = 0
        for w in words:
            self.execute('SELECT word_id FROM words WHERE (words.word=?)', w)
            word_ids = self.fetchall()
            self.execute('INSERT OR IGNORE INTO wordlist (word, word_ids) VALUES (?,?)', (w[0], repr(word_ids)))

            word_cnt += 1
            if word_cnt % print_step == 0:
                print "Ready", word_cnt*100/word_count, "%"

        self.__build_wordlist_index()

    def __get_word_forms(self, word_id):
        return self.__wf_shadow.get_object(word_id)

    def build_word_info(self, word):
        present_ids = []

        original_word = word

        ids = self.__wids_shadow.get_object(word)
        if ids is None:
            return None
        res = []
        for i, in ids:
            if i in present_ids:
                continue
            present_ids.append(i)

            entry = {}
            word_id, word, root, class_id = self.__w_shadow.get_object(i)
            present_ids.append(word_id)
            form = []
            if root == -1:
                # Word is primary
                entry["primary"] = {"word": word, "class_id": class_id}
                entry["forms"] = self.__get_word_forms(word_id)
            else:
                # Word is just form
                word_id, word, root, class_id = self.__w_shadow.get_object(root)
                if word_id in present_ids:
                    continue
                present_ids.append(word_id)
                entry["primary"] = {"word": word, "class_id": class_id}
                entry["forms"] = self.__get_word_forms(word_id)

            if entry["primary"]["word"] == original_word:
                class_id = entry["primary"]["class_id"]
                form.append({"word": original_word, "class_id": class_id, "info": self.get_class_info(class_id)})
            for f in entry["forms"]:
                if f["word"] == original_word:
                    class_id = f["class_id"]
                    form.append({"word": original_word, "class_id": class_id, "info": self.get_class_info(class_id)})
            entry["form"] = form
            res.append(entry)
        return res

    def word_info_str(self, info):
        return json.dumps(info, ensure_ascii=False)

    def add_words(self, words_iter, max_count=None):
        count = 0
        self.alphabet = [l for n, l in self.get_alphabet()]
        self.__drop_word_index()
        self.execute('PRAGMA synchronous=0;')

        wf = MorfWordGroup()
        while words_iter.has_data() and (max_count is None or count < max_count):
            line = words_iter.get()
            if len(line) <= 6:
                if wf.len() == 0:
                    continue
                self.add_word_group(wf)
                self.add_primary(wf)
                wf = MorfWordGroup()
                if count % 1000 == 0:
                    print "Inserted", count, "lines"
                continue

            w, i = self.line_to_form(line)
            w = w.strip()
            if not self.check_word(w):
                continue

            wf.add_entry(w, i)

            if max_count is not None and count >= max_count:
                break
            count += 1
        self.__build_word_index()

    def build_optimized(self, max_count=None):
        odb = OptimizedDbBuilder(reuse_db=self, rw=True)
        odb.build(max_count)

    def count_words(self, word_iter, max_count=None):
        wdc = WorddbCounter(reuse_db=self, rw=True)
        wdc.add_words(word_iter, max_count)

    def update_wordlist(self, wle):
        if wle is None:
            return
        self.execute('UPDATE wordlist SET word=?, cnt=? WHERE (wordlist.uword_id=?);', (wle.get_word(), wle.get_count(), wle.get_uword_id()))

    def get_primary_info(self, primary_word_form):
        return self.__pf_shadow.get_object(primary_word_form, cache_none=True)

    def flush_primaries(self):
        self.__pf_shadow.flush()


class OptimizedDbBuilder(common.db.Db):
    def __init__(self, reuse_db, rw=False):
        self.__dbbuild = reuse_db
        common.db.Db.__init__(self, reuse_db=reuse_db, rw=rw)

    def __insert_blob(self, word, word_id, blob):
        self.execute('INSERT INTO word_blobs (word, word_id, blob) VALUES (?, ?, ?)', (word, word_id, blob))

    def __drop_optimized_table(self):
        print "Dropping existing optimized tables..."
        self.execute('DROP INDEX IF EXISTS word_blobs_bw_idx;')
        self.execute('DROP INDEX IF EXISTS word_blobs_bi_idx;')
        self.execute('DROP TABLE IF EXISTS word_blobs;')
        self.commit()

        print "Running vacuum..."
        self.execute('VACUUM;')
        self.commit()

    def __create_optimized_table(self):
        print "Creating new optimized tables..."
        self.execute('CREATE TABLE IF NOT EXISTS word_blobs (word TEXT, word_id INTEGER, blob TEXT);')
        self.commit()

    def __disable_synchronous_mode(self):
        print "Disabling synchronous mode..."
        self.mksync()

    def __build_index(self):
        print "Creating index on words..."
        self.execute('CREATE INDEX IF NOT EXISTS word_blobs_bw_idx ON word_blobs (word) ;')
        print "Creating index on word ids..."
        self.execute('CREATE INDEX IF NOT EXISTS word_blobs_bi_idx ON word_blobs (word_id) ;')
        self.commit()

    def __build_blobs(self, max_count=None, chunk_size=10000):
        print "Building word blobs..."
        offset = 0
        while True:
            self.execute('SELECT word, uword_id FROM wordlist LIMIT ? OFFSET ?;', (chunk_size, offset))
            word_word_ids = self.fetchall()
            res_len = len(word_word_ids)
            offset += res_len

            for word, uword_id in word_word_ids:
                info = self.__dbbuild.build_word_info(word)
                blob = self.__dbbuild.word_info_str(info)
                self.__insert_blob(word, uword_id, blob)
            self.commit()

            print offset, " entries complete"
            if res_len < chunk_size or (max_count is not None and max_count <= offset):
                break

    def build(self, max_count=None):
        print "Started to build optimized table"
        self.__drop_optimized_table()
        self.__create_optimized_table()
        self.__disable_synchronous_mode()
        self.__build_blobs(max_count)
        self.__build_index()
        self.commit()


class WorddbCounter(common.shadow.Shadow, common.db.Db):
    def __init__(self, reuse_db, rw=False):
        common.db.Db.__init__(self, reuse_db=reuse_db, rw=rw)
        self.__worddb = reuse_db

    def __log_progress(self, cnt):
        if cnt % 1000 == 0:
            print "Processed", cnt, "words"
        if cnt % 5000000 == 0:
            print "Flushing primaries..."
            self.__worddb.flush_primaries()
        if cnt % 100000 == 0:
            print "Running gc..."
            gc.collect()

    def add_words(self, words_iter, max_count=None):
        count = 0
        self.mksync()
        fail_cnt = 0

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
            used_primaries = []
            word_primaries = self.__worddb.get_word_primaries(word)

            count += 1

            if word_primaries is None:
                self.__log_progress(count)
                continue

            for pf in word_primaries:
                if pf in used_primaries:
                    continue
                used_primaries.append(pf)

                pfis = self.__worddb.get_primary_info(pf)
                if pfis is None:
                    continue
                for pfi in pfis:
                    pfi.increase_total_usage()
                    pfi.increase_form_usage(word)

            self.__log_progress(count)

        self.__worddb.flush_primaries()
        self.commit()


class WordClassesBuilder(base.WordClasses):
    def __init__(self, reuse_db):
        base.WordClasses.__init__(self, reuse_db=reuse_db, rw=True)
        self.__create_tables()

    def __create_tables(self):
        commands = ['CREATE TABLE IF NOT EXISTS word_classes (class_id INTEGER PRIMARY KEY, json_info TEXT, UNIQUE(json_info));', ]
        for c in commands:
            self.execute(c)
        self.commit()

    def add_class(self, json_info):
        self.execute('INSERT INTO word_classes (json_info) VALUES (?);', (json_info,))
        cid = self.get_lastrowid()
        self.json_to_id[json_info] = cid
        self.id_to_json[cid] = json_info

    def get_class_id(self, json_info):
        if self.json_to_id.has_key(json_info):
            return self.json_to_id[json_info]
        self.add_class(json_info)
        return self.json_to_id[json_info]

    def get_class_by_id(self, cid):
        return self.id_to_json[cid]
