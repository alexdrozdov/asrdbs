import common.config
import parser.spare.index
from parser.spare.wordform import WordFormFabric
from common.singleton import singleton


@parser.spare.index.tokenmapper(name='worddb-mapper')
@parser.spare.index.constructable
class WorddbTokenMapper(object):
    def __init__(self, cfg):
        super().__init__()
        self.__wff = WordFormFabric(cfg['worddb'])

    def map(self, tokens):
        return [
            self.__wff.create(word_pos_word[1], word_pos_word[0])
            for word_pos_word in enumerate(tokens)
        ]


class TokenMapperSelector(object):
    def __init__(self):
        self.__mapper = None
        cfg = common.config.Config()
        mapper_cfg = cfg['/parser/io/tokenmapper']
        mapper_cls = parser.spare.index.get(
            mapper_cfg['name'],
            namespace='tokenmapper'
        )
        self.__mapper = mapper_cls(mapper_cfg)

    def map(self, tokens):
        return self.__mapper.map(tokens)


@singleton
class TokenMapper(TokenMapperSelector):
    pass


def map_tokens(tokens):
    return TokenMapper().map(tokens)
