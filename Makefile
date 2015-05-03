MKDIR_P = mkdir -p

BUILD_DIR = build
DB_DIR = ./dbs
DATA_DIR = ./data
LIBRU_DIR = ../libru/book

MORF_FILE = ${DATA_DIR}/morh.txt

WORD_DB = ${DB_DIR}/worddb.db
LIBRU_DB = ${DB_DIR}/librudb.db

# WORD_LIMIT = -l 10000
# TEXT_LIMIT = -l 10

worddb_create = ${BUILD_DIR}/worddb_create.lf
worddb_wordlist = ${BUILD_DIR}/worddb_wordlist.lf
worddb_count = ${BUILD_DIR}/worddb_count.lf
worddb_optimize = ${BUILD_DIR}/worddb_optimize.lf

libru_list_file = ${BUILD_DIR}/libru.lst

all: librudb worddb

librudb: dirs ${LIBRU_DB} 

worddb: dirs ${WORD_DB}

worddb-create: rm_create ${worddb_create}

worddb-wordlist: rm_wordlist ${worddb_wordlist}

worddb-count: rm_count ${worddb_count}

worddb-optimize: rm_optimize ${worddb_count}

${LIBRU_DB}: ${libru_list_file}
	PYTHONPATH=`pwd` PYTHONIOENCODING=utf-8 ./builders/build_librudb.py ${TEXT_LIMIT} -a ${libru_list_file} ${LIBRU_DB}

${libru_list_file}:
	./builders/build_libru_list.sh ${LIBRU_DIR} ${libru_list_file}


${WORD_DB}: ${LIBRU_DB} ${worddb_count}

${worddb_create}:
	PYTHONPATH=`pwd` PYTHONIOENCODING=utf-8 ./builders/build_worddb.py ${WORD_LIMIT} -c -t ${MORF_FILE} ${WORD_DB}
	touch ${worddb_create}

${worddb_wordlist}: ${worddb_create}
	PYTHONPATH=`pwd` PYTHONIOENCODING=utf-8 ./builders/build_worddb.py -w ${WORD_DB}
	touch ${worddb_wordlist}

${worddb_optimize}:${worddb_wordlist}
	PYTHONPATH=`pwd` PYTHONIOENCODING=utf-8 ./builders/build_worddb.py -o ${WORD_DB}
	touch ${worddb_optimize}

${worddb_count}: ${LIBRU_DB} ${worddb_optimize}
	PYTHONPATH=`pwd` PYTHONIOENCODING=utf-8 ./builders/build_worddb.py ${WORD_LIMIT} -n -i ${LIBRU_DB} ${WORD_DB}
	touch ${worddb_count}

clean:
	rm -rf ${BUILD_DIR}

rm_create:
	rm -f ${worddb_create}

rm_wordlist:
	rm -f ${worddb_wordlist}

rm_count:
	rm -f ${worddb_count}

rm_optimize:
	rm -f ${worddb_optimize}


.PHONY: dirs

.PHONY: librudb

.PHONY: worddb

.PHONY: worddb-create

.PHONY: wordb-wordlist

.PHONY: worddb-count

.PHONY: worddb-optimize

dirs: ${BUILD_DIR} ${DB_DIR} 

${BUILD_DIR}:
	${MKDIR_P} ${BUILD_DIR}

${DB_DIR}:
	${MKDIR_P} ${DB_DIR}

