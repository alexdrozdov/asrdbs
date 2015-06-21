

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
        self.__states = []
        self.__name2state = {}
        self.__containers = []

    def __add_state(self, state):
        self.__states.append(state)
        self.__name2state[state.get_name()] = state
        if state.is_container():
            self.__containers.append(state)

    def __create_states(self, spec):
        for st in spec.iter_all_entries():
            state_name = self.gen_state_name(st)
            state = SpecStateDef(state_name, st)
            self.__add_state(state)

    def __create_single_level_trs(self, spec, base=None):
        spec_iter = spec.get_hierarchical_iter(base)

        for st in spec_iter.get_all_entries():
            state = self.__name2state[self.gen_state_name(st)]
            while True:
                st_next = spec_iter.get_after(st)
                if st_next is None:
                    break
                state_next = self.__name2state[self.gen_state_name(st_next)]
                state.add_trs_to(state_next)
                if st_next.is_required():
                    break  # No need to add anything further - we cant skip this state
            if state.is_repeated():
                state.add_trs_to(state)
            if state.is_container():
                self.add_container_to_process()
            if state.is_contained() and is_local_final:
                parent = state.get_parent_state()
                state.add_parent_trs(parent)

    def __create_upper_level_trs(self, spec):
        self.__create_single_level_trs(spec, base=None)

    def __create_lower_level_trs(self, spec):
        self.__containers_qq = [c for c in self.__containers]
        while len(self.__containers_qq):
            container = self.__containers_qq[0]
            self.__containers_qq.pop()
            st = container.get_spec()
            self.__create_single_level_trs(spec, st)

    def __create_downgrading_trs(self, spec):
        pass

    def __remove_containers(self):
        states = []
        for state in self.__states:
            if state.is_container():
                state.unlink_all()
                continue
            states.append(state)
        self.__states = states

    def compile(self, spec):
        self.__create_states(spec)
        self.__create_downgrading_trs(spec)
        self.__create_upper_level_trs(spec)
        self.__create_lower_level_trs(spec)
        self.__remove_containers()


class SpecStateDef(object):
    def __init__(self, name, spec_dict):
        self.__name = name
        self.__transitions = []
        self.__spec_dict = spec_dict


class SpecTrsDef(object):
    def __init__(self, from_state, to_state, conditions):
        self.__from_state = from_state
        self.__to_state = to_state
        self.__conditions = conditions

    def check(self, form):
        pass


class CompiledSpec(object):
    def __init__(self, src_spec):
        self.__src_spec = src_spec
        self.__states = []
        self.__name2state = {}
