import parser.io.tokenizer
import parser.io.tokenmapper
import parser.spare.wordform


class Sentence(object):
    def __init__(self, forms_array):
        self.__forms = forms_array

    def finalize(self):
        if not isinstance(self.__forms[-1], parser.spare.wordform.SentenceFini):
            self.__forms.append(parser.spare.wordform.SentenceFini())
        return self

    @staticmethod
    def from_string(s):
        tokens = parser.io.tokenizer.tokenize(s)
        forms = parser.io.tokenmapper.map_tokens(tokens)
        return Sentence(forms)

    @staticmethod
    def from_array(a):
        return Sentence([i for i in a])

    @staticmethod
    def from_sentence(s):
        return Sentence.from_string(s).finalize()

    def __iter__(self):
        return iter(self.__forms)


class InputContext(object):
    def __init__(self, ctx):
        self.__ctx = ctx

    def ctx(self):
        return self.__ctx


class SentenceInput(InputContext):
    def __init__(self, ctx):
        super().__init__(ctx)

    def push(self, sentence):
        tokenized_sentence = Sentence.from_sentence(sentence)
        self.ctx().push_sentence(tokenized_sentence)
