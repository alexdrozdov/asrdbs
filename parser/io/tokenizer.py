import re
import common.config
import parser.spare.index
from common.singleton import singleton


@parser.spare.index.tokenizer(name='re-tokenizer')
@parser.spare.index.constructable
class ReTokenizer(object):
    def __init__(self, cfg):
        super().__init__()

    def tokenize(self, string):
        if isinstance(string, list):
            return string
        return [s for s in re.sub(
            r'\.\s*$',
            r' . ',
            re.sub(
                r"(,\s)",
                r' \1',
                re.sub(
                    r"([^\w\.\-\/,])",
                    r' \1 ',
                    string,
                    flags=re.U
                ),
                flags=re.U
            ),
            flags=re.U
        ).split() if s]


class TokenizerSelector(object):
    def __init__(self):
        self.__tokenizer = None
        cfg = common.config.Config()
        tokenizer_cfg = cfg['/parser/io/tokenizer']
        tokenizer_cls = parser.spare.index.get(
            tokenizer_cfg['name'],
            namespace='tokenizer'
        )
        self.__tokenizer = tokenizer_cls(tokenizer_cfg)

    def tokenize(self, s):
        return self.__tokenizer.tokenize(s)


@singleton
class Tokenizer(TokenizerSelector):
    pass


def tokenize(s):
    return Tokenizer().tokenize(s)
