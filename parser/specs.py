

class SequenceSpec(object):
    def __init__(self):
        pass


class RequiredSpecs(object):
    def IsNecessary(self):
        pass

    def IsOptional(self):
        pass


class __pos_check(object):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def check(self, form):
        return form.get_pos() in self.__pos_names


class PosSpecs(object):
    def IsNoun(self):
        return __pos_check(["noun", ])

    def IsAdjective(self):
        return __pos_check(["adjective", ])

    def IsAdverb(self):
        return __pos_check(["adverb", ])

    def IsComma(self):
        return __pos_check(["comma", ])


class __position_spec(object):
    def __init__(self):
        pass


def PositionSpecs(object):
    def IsBefore(self):
        pass

    def SequenceEnd(self):
        pass


class LinkSpecs(object):
    def IsSlave(self):
        pass

    def MastersExcept(self):
        pass


class AdjNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self)
        self.__spec_name = 'adj+-noun'
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs.IsNecessary(),
                "id": "adj",
                "pos_type": [PosSpecs.IsAdjective(), ],
                "position": [PositionSpecs.IsBefore("noun"), ],
                "master-slave": [LinkSpecs.IsSlave("noun"), ],
                "unwanted-links": [LinkSpecs.MastersExcept("noun"), ],
                "add-to-seq": True
            },
            {
                "id": "adj+",
                "required": RequiredSpecs.IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "id": "comma",
                        "required": RequiredSpecs.IsNesessary(),
                        "pos_type": [PosSpecs.IsComma(), ],
                        "position": [PositionSpecs.IsBeforeIfExists("adv"), PositionSpecs.IsBefore('adj-seq')],
                        "add-to-seq": True
                    },
                    {
                        "id": "adv",
                        "required": RequiredSpecs.IsOptional(),
                        "pos_type": [PosSpecs.IsAdverb(), ],
                        "position": [PositionSpecs.IsBefore("adj-seq"), ],
                        "master-slave": [LinkSpecs.IsSlave("adj-seq"), ],
                        "add-to-seq": False
                    },
                    {
                        "id": "adj-seq",
                        "required": RequiredSpecs.IsNesessary(),
                        "pos_type": [PosSpecs.IsAdjective(), ],
                        "position": [PositionSpecs.IsBefore("noun"), ],
                        "master-slave": [LinkSpecs.IsSlave("noun"), ],
                        "unwanted-links": [LinkSpecs.MastersExcept("noun"), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "id": "noun",
                "required": RequiredSpecs.IsNecessary(),
                "pos_type": [PosSpecs.IsNoun(), ],
                "position": [PositionSpecs.SequenceEnd(), ],
                "add-to-seq": True
            }
        ]


class SpecCompiler(object):
    def __init__(self):
        pass

    def compile(self, spec):
        pass


class CompiledSpec(object):
    def __init__(self, src_spec):
        self.__src_spec = src_spec
