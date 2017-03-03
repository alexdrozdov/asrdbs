import parser.spare
from parser.lang.base.rules.defs import WordSpecs


@parser.spare.at(name='word', namespace=None)
@parser.spare.constructable
def word(body, *args, **kwargs):
    word_list = body.popaslist('@word')
    body.setkey("pos_type", WordSpecs().IsWord(word_list))


@parser.spare.at(name='word-forms', namespace=None)
@parser.spare.constructable
def wordforms(body, *args, **kwargs):
    word_list = body.popaslist('@word-forms')
    body.setkey("pos_type", WordSpecs().IsWord(word_list))
