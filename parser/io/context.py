import parser.io.sentence
import parser.engine.matched


class InputContext(object):
    def __init__(self, ctx):
        self.__ctx = ctx

    def ctx(self):
        return self.__ctx


class SentenceInput(InputContext):
    def __init__(self, ctx):
        super().__init__(ctx)

    def push(self, sentence):
        tokenized_sentence = parser.io.sentence.Sentence.from_sentence(sentence)
        self.ctx().push_sentence(tokenized_sentence)


class OutputContext(object):
    def __init__(self, ctx):
        self.__ctx = ctx
        self.__next = None
        ctx.attach(self)

    def attach(self, ctx):
        self.__next = ctx

    def call_next(self, fcn_name, *args, **kwargs):
        if self.__next is not None:
            fcn = getattr(self.__next, fcn_name)
            fcn(*args, **kwargs)

    def sequence_forked(self, ctx, sq, new_sq):
        self.call_next('sequence_forked', ctx, sq, new_sq)

    def sequence_forking(self, ctx, sq):
        self.call_next('sequence_forking', ctx, sq)

    def sequence_matched(self, ctx, sq):
        self.call_next('sequence_matched', ctx, sq)

    def sequence_failed(self, ctx, sq):
        self.call_next('sequence_failed', ctx, sq)

    def sequence_res(self, ctx, res):
        self.call_next('sequence_res', ctx, res)

    def ctx_create(self, ctx):
        self.call_next('ctx_create', ctx)

    def ctx_complete(self, ctx):
        self.call_next('ctx_complete', ctx)


class OutputChainWrapper(object):
    def __init__(self, first, last):
        self.__first = first
        self.__last = last

    def __iter__(self):
        return iter(self.__last)


class ToMatchedSequence(OutputContext):
    def __init__(self, ctx):
        super().__init__(ctx)

    def sequence_matched(self, ctx, sq):
        ms = parser.engine.matched.MatchedSequence(sq)
        self.call_next('matched', ms)


class MostComplete(OutputContext):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.__buffer = []
        self.__max_length = 0

    def matched(self, ms):
        l = ms.get_entry_count(hidden=False, virtual=False)
        if self.__max_length < l:
            self.__buffer = [ms, ]
            self.__max_length = l
        elif self.__max_length == l:
            self.__buffer.append(ms)

    def ctx_complete(self, ctx):
        for ms in self.__buffer:
            self.call_next('matched', ms)
        self.__max_length = 0
        self.__buffer = []


class IgnoreDuplicate(OutputContext):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.__hashes = set()

    def matched(self, ms):
        h = hash(ms)
        if h not in self.__hashes:
            self.__hashes.add(h)
            self.call_next('nonduplicate', ms)


class Store(OutputContext):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.__sequences = []

    def nonduplicate(self, ms):
        self.__sequences.append(ms)

    def __iter__(self):
        return iter(self.__sequences)
