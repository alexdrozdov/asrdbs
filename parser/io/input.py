import uuid
import weakref
import parser.io.mappers
import parser.io.tokenizers


class Term(object):
    """
    Term represents entries inside flow graph
    """

    def __init__(self):
        self.__uuid = uuid.uuid1()
        self.__next = []
        self.__prev = []

    def uuid(self):
        return self.__uuid

    def next(self):
        return self.__next

    def prev(self):
        return self.__prev

    def __lshift__(self, other):
        other >> self
        self.__next.append(other)
        other.__prev.append(self)
        return other

    def __rshift__(self, other):
        pass


class Lexical(Term):
    """
    Lexical is subclass of Term and represents one independent lixical form
    in sequence.

    Shall point to some WordForm

    Is allowed to reference directly next Lexical term or Transition

    Previous entry may be weak reference only
    """

    def __init__(self, wf):
        super().__init__()
        self.__wf = wf

    def __lshift__(self, other):
        if self.__next:
            raise RuntimeError(
                'Tried to add more than one reference to Lexical Term')
        return super.__lshift__(other)

    def __rshift__(self, other):
        if self.__prev:
            raise RuntimeError(
                'Tried to add more than one reference to Lexical Term')

    def bounds(self):
        return Bounds(left=self, right=self)


class Transition(Term):
    """
    Transition is subclass of Term and represents some transition between
    Lexical terms

    Transition may reference any forwarding terms, either Lexical or Transitions
    """

    def __init__(self):
        super().__init__()

    def __lshift__(self, other):
        super.__lshift__(other)

    def __rshift__(self, other):
        pass

    def bounds(self):
        return Bounds(left=self, right=self)


class View(object):
    """
    View represents any set of terms
    View doesnt own terms but can reference them to provide iterators or methods
    to operarate with.
    """
    pass


class Bounds(View):
    """
    Bounds represents range of terms
    References the most left and right terms of range
    """

    def __init__(self, left, right):
        super().__init__()
        self.__left = weakref.proxy(left)
        self.__right = weakref.proxy(right)

    def left(self):
        return self.__left

    def right(self):
        return self.__right


class Parallel(View):
    """
    Represents set of independent terms or views that can take place
    simultaniously. Any terms, terms sequnces or bounds will be put inside
    wrappers as parallel.
    Is subclass of view. Should be used only for grouping terms into desired
    order
    """

    def __init__(self, info=None):
        self.__info = info
        self.__lb = Transition()
        self.__rb = Transition()

    def __lshift__(self, other):
        self.__lt << other << self.__rt

    def bounds(self):
        return Bounds(left=self.__lt, right=self.__rt)


class Sequential(View):
    """
    Represents set of sequencial independent terms or views. Any independent
    terms, views or bounds will be linked with last term, view or bound.
    Is subclass of view. Should be used only for grouping terms into desired
    order
    """

    def __init__(self, text):
        self.__first = None
        self.__last = None

    def first(self):
        return self.__first

    def last(self):
        return self.__last

    def __lshift__(self, term):
        """
        Append flow with term
        Term is linked to the last term appended

        Return:
            Provided term
        """

        bounds = term.bounds()
        if self.__first is None:
            self.__first = bounds.left()
        else:
            self.__last << bounds.left()
        self.__last = bounds.right()
        return self.__last

    def bounds(self):
        return Bounds(self.__first, self.__last)


class SimpleSequence(Sequential):
    """Provides iterators for flow inspecting
    Is basic flow class just for iterating flow, should be specilized for
    any flow type, i.e. grammatically correct text sentences, fuzzy text
    sentences, fuzzy sequences from ASR frontend, etc

    """
    def __init__(self, mapper=None):
        super().__init__()
        if mapper is None:
            mapper = parser.io.mappers.DefMapper()
        self.__mapper = mapper

    def __lshift__(self, term):
        p = Parallel(origin=term)
        for wf in self.__mapper.map(term):
            p << Lexical(wf)
        super.__lshift__(p)


class StaticSentence(SimpleSequence):
    def __init__(self, text, mapper=None, tokenizer=None):
        super.__init__(mapper=mapper)
        if tokenizer is None:
            tokenizer = parser.io.tokenizers.DefTokenizer()
        self.__tokenizer = tokenizer
        self.__text = text
        for t in self.__tokenizer.tokenize(text):
            super().__lshift__(t)
