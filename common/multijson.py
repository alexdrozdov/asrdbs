import re
import json


class MultiJson(object):
    """MultiJson - load multiple json objects from a signle string

    MultiJson splits provided string into several json objects. Split algorithm
    is determined with splitter argument:
        - splitter_comment_regex option expects json objects to be separated
        with comments starting from beginning of line with '#' symbol.
        Next json object should be started from the new line.
        Any characters after '#' symbols are treated as comments and removed till
        line break. This also corresponds to '#' symbols inside textual values.
        splitter_comment_regex option should be used if no any values contain
        '#' symbols. Otherwise use splitter_match_braces

        - splitter_match_braces option matches opening and closing braces. Any
        symbol sequence between matched upper level braces is supposed to json
        object.
        '#' symbols outside of textual values are treated as comments and
        removed till line break. '#' inside of textual values are ignored.

    Note:
        - splitter_comment_regex is expected to act faster then
        splitter_match_braces and shall be prefered for the large files if
        theirs content meets algorithm requirements.

        - any empty lines surrounding json objects are ignored

    Example:

        >> test_json = {
        >>     # Greet the World
        >>     "hello": "world",
        >>     "our": {
        >>         "names": "are",
        >>         "stored": {
        >>             "list": [
        >>                 "Foo", # Let him be first on list
        >>                 "Baz",
        >>                 "Bar"  # We are not together
        >>             ],
        >>             "count": 3
        >>         }
        >>     }
        >> }
        >> #
        >> {
        >>     "its": [
        >>         "another",
        >>         "json",
        >>         "example",
        >>         {
        >>             "with": {
        >>                 "dictionary": [
        >>                     "inside",
        >>                     "list"
        >>                 ]
        >>             }
        >>         }
        >>     ]
        >> }
        >>
        >> mj = MultiJson(test_json, splitter=MultiJson.splitter_comment_regex)
        >> for j in mj.dicts():
        >>     print('<{j}>'.format(j=j))

        This will provide following output:
        >> <{'hello': 'world', 'our': {'names': 'are', 'stored': {'list': ['Foo', 'Baz', 'Bar'], 'count': 3}}}>
        >> <{'its': ['another', 'json', 'example', {'with': {'dictionary': ['inside', 'list']}}]}>
    """

    splitter_comment_regex = 1
    splitter_match_braces = 2

    def __init__(self, data, splitter=splitter_match_braces):
        """Constructs new MultiJson instance

        Args:
            data (string): string to be splitted to json objects

            splitter (int, optional): split algorithm. Read more in class-level
            description.
        """

        self.__jsons = list(self.__split(data, splitter))

    def jsons(self):
        """Returns list of textual json objects exctracted from string. To
        obtain Python dicts each string entry is expected to be explicitly
        parsed by caller.
        """
        return self.__jsons

    def dicts(self):
        """Returns list of dict objects exctracted from string. Each json object
        is parsed inside this fuction.
        """
        return [json.loads(s) for s in self.__jsons]

    def __split(self, data, method):
        if method == MultiJson.splitter_comment_regex:
            yield from self.__split_with_regexp(data)
        elif method == MultiJson.splitter_match_braces:
            yield from self.__split_by_braces(data)
        else:
            raise ValueError('Unsupported splitter code {0}'.format(method))

    def __split_with_regexp(self, data):
        for s in [_f for _f in re.split(
            '^#.*\n',
            data,
            flags=re.MULTILINE
        ) if _f]:
            yield re.sub('#.*\n', '\n', s, flags=re.MULTILINE).strip()

    def __split_by_braces(self, data):
        state = SplitterState(data)
        while state.has_data():
            while True:
                try:
                    if state.state() == SplitterState.BASE:
                        yield from self.__on_none(state)
                    elif state.state() == SplitterState.STRING:
                        self.__on_string(state)
                    elif state.state() == SplitterState.COMMENT:
                        self.__on_comment(state)
                except OnceMoreError:
                    continue
                break

        if state.state() == SplitterState.STRING:
            raise ValueError('Non closed string literal')
        if 0 != state.depth():
            raise ValueError('Non closed { found')

    def __on_comment(self, state):
        if state.cur() == '\n' or state.cur() == '\n':
            state.leave()
            return False

        state.skip(store=False)

    def __on_string(self, state):
        if state.cur() == '\\':
            if not state.cur_eq('\\\\') and not state.cur_eq('\\"'):
                raise ValueError('Wrong escape sequence at {l}:{c}'.format(
                    l=state.line(), c=state.col())
                )
            state.skip()
        elif state.cur() == '"':
            state.leave()

        state.skip()

    def __on_none(self, state):
        if state.cur() == '#':
            state.enter_comment()
            state.skip(store=False)
            return

        elif state.cur() == '"':
            state.enter_string()
        elif state.cur() == '{':
            state.step_in()
        elif state.cur() == '}':
            state.step_out()
            if state.depth() == 0:
                state.skip()
                yield state.chunk().strip()
                return

        state.skip()


class MultiJsonFile(MultiJson):
    """MultiJson - load multiple json objects from a single file

    Refer to MultiJson description for more details on attribuutes and behavior
    """

    def __init__(self, filename, splitter=MultiJson.splitter_match_braces):
        """Constructs new MultiJson instance

        Args:
            filename (string): file name containing jsons to load

            splitter (int, optional): split algorithm. Read more in MultiJson
            description.
        """

        with open(filename) as f:
            data = f.read()
            super().__init__(data, splitter=splitter)


class SplitterState(object):
    """Incapsulates parser state. For internal usage
    """

    BASE = 0
    STRING = 1
    COMMENT = 2

    def __init__(self, data):
        self.__data = data
        self.__len = len(data)
        self.__state = SplitterState.BASE
        self.__chunk = ''

        self.pos = 0

        self.__depth = 0
        self.__chunk = ''
        self.__line_cnt = 1
        self.__col_cnt = 1

    def cur(self):
        return self.__data[self.pos]

    def cur_eq(self, s):
        l = len(s)
        if self.__len <= self.pos + l:
            return False
        return self.__data[self.pos:self.pos + l] == s

    def skip(self, count=1, s=None, store=True):
        if store:
            self.__chunk += self.cur()

        if self.cur() == '\n':
            self.__line_cnt += 1
            self.__col_cnt = 1
        else:
            self.__col_cnt += 1

        if s is None:
            self.pos += count
        else:
            self.pos += len(s)

    def step_in(self):
        self.__depth += 1

    def step_out(self):
        assert 0 < self.__depth
        self.__depth -= 1

    def depth(self):
        return self.__depth

    def state(self):
        return self.__state

    def enter_string(self):
        assert self.__state == SplitterState.BASE
        self.__state = SplitterState.STRING

    def enter_comment(self):
        assert self.__state == SplitterState.BASE
        self.__state = SplitterState.COMMENT

    def leave(self):
        self.__state = SplitterState.BASE

    def chunk(self):
        c = self.__chunk
        self.__chunk = ''
        return c

    def has_data(self):
        return self.pos < self.__len

    def line(self):
        return self.__line_cnt

    def col(self):
        return self.__col_cnt


class OnceMoreError(Exception):
    """Invoked while parsing string with json objects to rerun analysis on
    current symbol. For internal usage.
    """

    pass
