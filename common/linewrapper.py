class LineWrapper(object):
    def __init__(self, prefered_length, max_length, splitters, indent=0, step=False):
        self.__prefered_length = prefered_length
        self.__max_length = max_length
        if isinstance(splitters, (list, tuple)):
            self.__wrapper_fcn = self.__wrap_sequence
        elif isinstance(splitters, str):
            self.__wrapper_fcn = self.__wrap_symbol
        else:
            raise ValueError(
                'Unsupported splitters format {0}'.format(type(splitters))
            )
        self.__splitters = dict(
            map(
                lambda i_s: (i_s[1], 1.0 / i_s[0]),
                enumerate(splitters, 1)
            )
        )
        self.__indent = indent
        self.__step = step

    def wrap(self, line, linebreak=None, indent_char=None):
        parts = self.__wrap(line)
        if linebreak is None:
            linebreak = '\r\n'
        if indent_char is None:
            indent_char = ' '
        indent = indent_char * self.__indent
        return linebreak.join(
            map(
                lambda i_p: i_p[1] if i_p[0] == 0 else indent + i_p[1] if i_p[0] == 1 or not self.__step else indent * i_p[0] + i_p[1],
                enumerate(parts)
            )
        )

    def __wrap(self, line, depth=0, indent=0):
        return self.__wrapper_fcn(line, depth, indent)

    def __wrap_symbol(self, line, depth=0, indent=0):
        if self.__step and 1 < depth:
            indent = indent * (depth - 1)
        max_length = self.__max_length - indent
        prefered_length = self.__prefered_length - indent

        if len(line) < max_length:
            return [line, ]

        max_rate = {
            'pos': max_length - 1,
            'rate': 0.0
        }
        for i in range(0, max_length):
            rate = {
                'pos': i,
                'rate': (self.__symbol_rate(line[i]) /
                         max(1.0, abs(i - prefered_length)))
            }
            if max_rate['rate'] < rate['rate']:
                max_rate = rate

        r = [line[0:max_rate['pos']], ]
        r.extend(
            self.__wrap(
                line[max_rate['pos']:],
                depth=depth + 1,
                indent=self.__indent
            )
        )
        return r

    def __wrap_sequence(self, line, depth=0, indent=0):
        if self.__step and 1 < depth:
            indent = indent * (depth - 1)
        max_length = self.__max_length - indent
        prefered_length = self.__prefered_length - indent

        if len(line) < max_length:
            return [line, ]

        max_rate = {
            'pos': max_length - 1,
            'rate': 0.0
        }
        for i in range(0, max_length):
            splitter = ''
            for s in list(self.__splitters.keys()):
                if max_length <= len(s) + i:
                    continue
                if line[i:i+len(s)] == s:
                    splitter = s
                    break

            rate = {
                'pos': i + len(splitter),
                'rate': (self.__symbol_rate(splitter) /
                         max(1.0, abs(i - prefered_length)))
            }
            if max_rate['rate'] < rate['rate']:
                max_rate = rate

        r = [line[0:max_rate['pos']], ]
        r.extend(
            self.__wrap(
                line[max_rate['pos']:],
                depth=depth + 1,
                indent=self.__indent
            )
        )
        return r

    def __symbol_rate(self, s):
        if s in self.__splitters:
            return self.__splitters[s]
        return 0.0
