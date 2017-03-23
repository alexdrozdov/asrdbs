import copy
import parser.spare


@parser.spare.at(name='brief', namespace='specs')
@parser.spare.constructable
def dependency_of(body, *args, **kwargs):
    br = body.pop('@brief')
    definitions = copy.deepcopy(br.pop('definitions'))
    formats = br.pop('formats')
    export = br.pop('export')
    for f in formats:
        b = to_brief(f)
        definitions[b.name()] = b

    exported = []
    for e in export:
        spec = definitions[e].format('spec', definitions=definitions)
        exported.append(spec)

    if 1 == len(exported):
        body['entries'] = exported[0]
    else:
        body['uniq-items'] = [
            {"@id": None,
             "@inherit": ["once"],
             "entries": e
             } for e in exported
        ]

    parser.spare.again()


def to_brief(fmt):
    p = Parser()
    return p.parse(fmt)


class UnacceptableTerm(RuntimeError):
    def __init__(self, current_class, supplied_class, symbol):
        super().__init__(
            'Class {0} doesnt support enclosed class {1} ({2})'.format(
                current_class, supplied_class, symbol)
        )


class BraceMismatch(RuntimeError):
    def __init__(self, current_class, supplied_class, symbol):
        super().__init__(
            'Found uballanced closer {2} for class {1} inside {0}'.format(
                current_class, supplied_class, symbol)
        )


class TermClosed(Exception):
    pass


class CloseAndRerun(Exception):
    pass


class Parser(object):
    def __init__(self):
        self.__stack = [Expression(self)]
        self.__openers = {
            '{': Entry, '<': Variant, '[': Optional, '(': Group,
            ' ': Idle, '\t': Idle, '+': Repeatable, '*': Any}
        for s in Text.alphabet:
            self.__openers[s] = Text
        self.__closers = {
            '}': Entry, '>': Variant, ']': Optional, ')': Group}

    def parse(self, string):
        for s in string:
            opener_class = self.__openers.get(s, None)
            closer_class = self.__closers.get(s, None)
            try:
                while True:
                    try:
                        self.__stack[-1].handle(s, opener_class, closer_class)
                    except CloseAndRerun:
                        self.__stack = self.__stack[0:-1]
                        continue
                    break
            except TermClosed:
                self.__stack = self.__stack[0:-1]
        return self.__stack[0]

    def push(self, term):
        self.__stack.append(term)


class Term(object):
    def __init__(self, owner, opener, closer, acceptable_terms):
        self._owner = owner
        self._opener = opener
        self._closer = closer
        self._acceptable_terms = acceptable_terms

    def _is_closer(self, s):
        return s == self._closer

    def _close(self):
        raise TermClosed()

    def _store_enclosed(self, term):
        raise RuntimeError('Unimplemented')

    def owner(self):
        return self._owner

    def _symbol(self, s):
        pass

    def handle(self, s, opener_class, closer_class):
        if closer_class is not None and closer_class != self.__class__:
            raise BraceMismatch(self.__class__, closer_class, s)
        if opener_class is not None:
            if opener_class not in self._acceptable_terms:
                raise UnacceptableTerm(self.__class__, opener_class, s)
            e = opener_class(self.owner())
            e._symbol(s)
            self._store_enclosed(e)
            self.owner().push(e)
            return

        if self._is_closer(s):
            self._close()


class Expression(Term):
    def __init__(self, owner):
        super().__init__(owner, None, None,
                         [Idle, Text, Entry, Optional, Variant, Group])
        self.__name = None
        self._enclosed = []

    def name(self):
        assert self.__name is not None
        return str(self.__name)

    def _store_enclosed(self, term):
        if isinstance(term, Idle):
            return
        if self.__name is None:
            self.__name = term
            return
        self._enclosed.append(term)

    def __repr__(self):
        return 'Expression({0})'.format(
            ', '.join([repr(e) for e in self._enclosed]))

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        if fmt == 'spec':
            return self.__fmt_spec(kwargs['definitions'])
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return str(self.__name) + ': ' + ' '.join(
            [e.format('brief') for e in self._enclosed])

    def __fmt_spec(self, definitions):
        return [e.format('spec',
                         definitions=definitions) for e in self._enclosed]


class Idle(Term):
    def __init__(self, owner):
        super().__init__(owner, None, None,
                         [Text, Entry, Optional, Variant, Group])

    def handle(self, s, opener_class, closer_class):
        if s not in ' \t':
            self._close()

    def _close(self):
        raise CloseAndRerun()

    def __repr__(self):
        return 'Idle()'

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return ' '


class Repeatable(Term):
    def __init__(self, owner):
        super().__init__(owner, '+', None, [])

    def handle(self, s, opener_class, closer_class):
        self._close()

    def _close(self):
        raise CloseAndRerun()

    def __repr__(self):
        return 'Repeatable()'

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return '+'


class Any(Term):
    def __init__(self, owner):
        super().__init__(owner, '*', None, [])

    def handle(self, s, opener_class, closer_class):
        self._close()

    def _close(self):
        raise CloseAndRerun()

    def __repr__(self):
        return 'Repeatable()'

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return '+'


class Text(Term):

    alphabet = """
    ,.1234567890
    abcdefghijklmnopqrstuvwxyz
    ABCDEFGHIJKLMNOPQRSTUVWXYZ
    абвгдеёжзийклмнопрстуфхцчшщъыьэюя
    АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ
    """.replace(' ', '').replace('\r', '').replace('\n', '')

    def __init__(self, owner):
        super().__init__(owner, None, ' ', [])
        self.__value = ''

    def handle(self, s, opener_class, closer_class):
        if opener_class == Text:
            self.__value += s
            return
        self._close()

    def _symbol(self, s):
        self.__value += s

    def _is_closer(self, s):
        return s not in Text.alphabet

    def _close(self):
        raise CloseAndRerun()

    def __repr__(self):
        return 'Text({0})'.format(str(self.__value))

    def __str__(self):
        return self.__value

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        if fmt == 'spec':
            return self.__fmt_spec(kwargs['definitions'])
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return self.__value

    def __fmt_spec(self, definitions):
        return {
            "@id": None,
            "@inherit": ['once'],
            "@word": [str(self.__value), ]
        }


class Entry(Term):
    def __init__(self, owner):
        super().__init__(owner, '{', '}', [Idle, Text])
        self._name = None

    def _store_enclosed(self, term):
        if isinstance(term, Idle):
            return
        if self._name is not None:
            raise RuntimeError('Additional Text for entry')
        self._name = term

    def __repr__(self):
        return 'Entry({0})'.format(str(self._name))

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        if fmt == 'spec':
            return self.__fmt_spec(kwargs['definitions'])
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return '{{{0}}}'.format(str(self._name))

    def __fmt_spec(self, definitions):
        value = definitions[str(self._name)]
        if isinstance(value, Expression):
            return {
                "@id": None,
                "@inherit": ["once"],
                "entries": value.format('spec', definitions=definitions)
            }
        else:
            return value


class Optional(Term):
    def __init__(self, owner):
        super().__init__(
            owner, '[', ']',
            [Idle, Text, Entry, Optional, Variant, Group, Repeatable, Any])
        self._enclosed = []
        self.__repeatable = False
        self.__any = False

    def _store_enclosed(self, term):
        if isinstance(term, Idle):
            return
        if isinstance(term, Repeatable):
            self.__repeatable = True
            return
        if isinstance(term, Any):
            self.__any = True
            return
        self._enclosed.append(term)

    def __repr__(self):
        return 'Optional({0})'.format(
            ', '.join([repr(e) for e in self._enclosed]))

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        if fmt == 'spec':
            return self.__fmt_spec(kwargs['definitions'])
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return '[{0}{1}]'.format(
            '+' if self.__repeatable else '*' if self.__any else '',
            ' '.join([e.format('brief') for e in self._enclosed]))

    def __fmt_spec(self, definitions):
        if self.__repeatable:
            repeatable = 'once-or-more'
        elif self.__any:
            repeatable = 'any'
        else:
            repeatable = 'once-or-none'
        return {
            "@id": None,
            "@inherit": [repeatable],
            "entries": [e.format(
                'spec', definitions=definitions
            ) for e in self._enclosed]
        }


class Variant(Term):
    def __init__(self, owner):
        super().__init__(owner, '<', '>',
                         [Idle, Text, Entry, Optional, Variant, Group])
        self._enclosed = []

    def _store_enclosed(self, term):
        if isinstance(term, Idle):
            return
        self._enclosed.append(term)

    def __repr__(self):
        return 'Variant({0})'.format(
            ', '.join([repr(e) for e in self._enclosed]))

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        if fmt == 'spec':
            return self.__fmt_spec(kwargs['definitions'])
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return '<{0}>'.format(
            ' | '.join([e.format('brief') for e in self._enclosed]))

    def __fmt_spec(self, definitions):
        return {
            "@id": None,
            "@inherit": ['once'],
            "uniq-items": [e.format(
                'spec', definitions=definitions
            ) for e in self._enclosed]
        }


class Group(Term):
    def __init__(self, owner):
        super().__init__(owner, '(', ')',
                         [Idle, Text, Entry, Optional, Variant])
        self._enclosed = []

    def _store_enclosed(self, term):
        if isinstance(term, Idle):
            return
        self._enclosed.append(term)

    def __repr__(self):
        return 'Group({0})'.format(
            ', '.join([repr(e) for e in self._enclosed]))

    def format(self, fmt, *args, **kwargs):
        if fmt == 'brief':
            return self.__fmt_brief()
        if fmt == 'spec':
            return self.__fmt_spec(kwargs['definitions'])
        raise ValueError('Unsupported format {0}'.format(fmt))

    def __fmt_brief(self):
        return '({0})'.format(
            ' '.join([e.format('brief') for e in self._enclosed]))

    def __fmt_spec(self, definitions):
        return {
            "@id": None,
            "@inherit": ['once'],
            "entries": [e.format(
                'spec', definitions=definitions
            ) for e in self._enclosed]
        }


# formats = [
#     "r1: {a} [{p}] {n} [+ , {n}] [и {n} [+ , и {n}]]",
#     "r2: {a} ({p} {n}) [, ({p} {n})] [и ({p} {n}) [, и ({p} {n})]]",
#     "r3: {a} не только <{r1} | {r2}> [<но | да> и <{r1} | {r2}>]",
# ]
#
#
# p = Parser()
# r = p.parse(formats[2])
# print(repr(r))
#
#
# print(formats[2])
# print(r.format('brief'))