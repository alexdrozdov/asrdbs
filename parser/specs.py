import graph


class UniqEnum(object):
    def __init__(self):
        self.__uniq = 1

    def get_uniq(self):
        r = self.__uniq
        self.__uniq *= 2
        return r


ue = UniqEnum()


class SequenceSpec(object):
    def __init__(self):
        pass

    def get_spec(self):
        return self.spec


class FsmSpecs(object):
    init = 1
    fini = 2

    def IsInit(self):
        return FsmSpecs.init

    def IsFini(self):
        return FsmSpecs.fini


class RequiredSpecs(object):
    def IsNecessary(self):
        return True

    def IsOptional(self):
        return False


class c__pos_check(object):
    def __init__(self, pos_names):
        self.__pos_names = pos_names

    def check(self, form):
        return form.get_pos() in self.__pos_names


class PosSpecs(object):
    def IsNoun(self):
        return c__pos_check(["noun", ])

    def IsAdjective(self):
        return c__pos_check(["adjective", ])

    def IsAdverb(self):
        return c__pos_check(["adverb", ])

    def IsComma(self):
        return c__pos_check(["comma", ])


class __position_spec(object):
    def __init__(self):
        pass


class PositionSpecs(object):
    def IsBefore(self, id_name):
        pass

    def SequenceEnd(self):
        pass

    def IsBeforeIfExists(self, id_name):
        pass


class LinkSpecs(object):
    def IsSlave(self, id_name):
        pass

    def MastersExcept(self, id_name):
        pass


class AdjNounSequenceSpec(SequenceSpec):
    def __init__(self):
        SequenceSpec.__init__(self)
        self.__spec_name = 'adj+-noun'
        self.__compared_with = {}

        self.spec = [
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "init",
                "fsm": FsmSpecs().IsInit(),
                "add-to-seq": False
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "adj",
                "pos_type": [PosSpecs().IsAdjective(), ],
                "position": [PositionSpecs().IsBefore("noun"), ],
                "master-slave": [LinkSpecs().IsSlave("noun"), ],
                "unwanted-links": [LinkSpecs().MastersExcept("noun"), ],
                "add-to-seq": True
            },
            {
                "id": "adj+",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "id": "comma",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "position": [PositionSpecs().IsBeforeIfExists("adv"), PositionSpecs().IsBefore('adj-seq')],
                        "add-to-seq": True
                    },
                    {
                        "id": "adv",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsAdverb(), ],
                        "position": [PositionSpecs().IsBefore("adj-seq"), ],
                        "master-slave": [LinkSpecs().IsSlave("adj-seq"), ],
                        "add-to-seq": False
                    },
                    {
                        "id": "adj-seq",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsAdjective(), ],
                        "position": [PositionSpecs().IsBefore("noun"), ],
                        "master-slave": [LinkSpecs().IsSlave("noun"), ],
                        "unwanted-links": [LinkSpecs().MastersExcept("noun"), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "id": "adj++",
                "required": RequiredSpecs().IsOptional(),
                "repeatable": True,
                "entries":
                [
                    {
                        "id": "and",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsComma(), ],
                        "position": [PositionSpecs().IsBeforeIfExists("adv"), PositionSpecs().IsBefore('adj-seq')],
                        "add-to-seq": True
                    },
                    {
                        "id": "adv++",
                        "required": RequiredSpecs().IsOptional(),
                        "pos_type": [PosSpecs().IsAdverb(), ],
                        "position": [PositionSpecs().IsBefore("adj-seq"), ],
                        "master-slave": [LinkSpecs().IsSlave("adj-seq"), ],
                        "add-to-seq": False
                    },
                    {
                        "id": "adj-seq++",
                        "required": RequiredSpecs().IsNecessary(),
                        "pos_type": [PosSpecs().IsAdjective(), ],
                        "position": [PositionSpecs().IsBefore("noun"), ],
                        "master-slave": [LinkSpecs().IsSlave("noun"), ],
                        "unwanted-links": [LinkSpecs().MastersExcept("noun"), ],
                        "add-to-seq": True
                    },
                ]
            },
            {
                "id": "noun",
                "required": RequiredSpecs().IsNecessary(),
                "pos_type": [PosSpecs().IsNoun(), ],
                "position": [PositionSpecs().SequenceEnd(), ],
                "add-to-seq": True
            },
            {
                "required": RequiredSpecs().IsNecessary(),
                "id": "fini",
                "fsm": FsmSpecs().IsFini(),
                "add-to-seq": False
            },
        ]


class SequenceSpecIter(object):
    def __init__(self, l):
        self.__l = l

    def get_all_entries(self):
        return self.__l

    def get_after(self, entry):
        try:
            i = self.__l.index(entry)
            return self.__l[i + 1]
        except:
            return None


class IterableSequenceSpec(SequenceSpec):
    def __init__(self, spec):
        self.__basic_spec = spec.get_spec()
        self.__index_all_entries()
        self.__index_layers()
        self.__index_hierarchy()

    def __index_subentries(self, item, level):
        for st in item["entries"]:
            self.__set_state_uid(st)
            self.__set_state_level(st, level)
            self.__all_entries.append(st)
            if st.has_key("entries"):
                self.__index_subentries(st, level + 1)

    def __index_all_entries(self):
        self.__all_entries = []
        level = 0
        for st in self.__basic_spec:
            self.__set_state_uid(st)
            self.__set_state_level(st, level)
            self.__all_entries.append(st)
            if st.has_key("entries"):
                self.__index_subentries(st, level + 1)

    def __index_layer(self, subspec, layer=0):
        if len(self.__layers) <= layer:
            self.__layers.append([])
        l_list = self.__layers[layer]
        for st in subspec:
            l_list.append(st)
            if st.has_key("entries"):
                self.__index_layer(st["entries"], layer=layer+1)

    def __index_layers(self):
        self.__layers = []
        self.__index_layer(self.__basic_spec)

    def __set_state_uid(self, state):
        if state.has_key("uid"):
            return
        state["uid"] = ue.get_uniq()

    def __set_state_level(self, state, level):
        state["level"] = level

    def __add_child_to_parent(self, child, parent):
        self.__parents[child["uid"]] = parent

    def __index_item_entries(self, item):
        l = []
        if item.has_key("entries"):
            for st in item["entries"]:
                l.append(st)
                self.__add_child_to_parent(st, item)
                self.__index_item_entries(st)
        self.__hierarchy[item["uid"]] = l

    def __index_hierarchy(self):
        self.__hierarchy = {}
        self.__parents = {}

        basic_list = []
        for st in self.__basic_spec:
            basic_list.append(st)
            self.__index_item_entries(st)
        self.__hierarchy[None] = basic_list

    def get_level_count(self):
        return len(self.__layers)

    def get_state_iter(self):
        return SequenceSpecIter(self.__all_entries)

    def get_parent(self, item):
        return self.__parents[item["uid"]]

    def get_hierarchical_iter(self, base):
        if base is None:
            return SequenceSpecIter(self.__hierarchy[None])
        return SequenceSpecIter(self.__hierarchy[base["uid"]])

    def get_level_iter(self, level):
        return SequenceSpecIter(self.__layers[level])

    def get_child_iter(self, base):
        return self.get_hierarchical_iter(base)


class SpecCompiler(object):
    def __init__(self):
        self.__states = []
        self.__name2state = {}
        self.__containers = []
        self.__containers_qq = []

    def gen_state_name(self, st):
        return st["id"]

    def __add_state(self, state):
        self.__states.append(state)
        self.__name2state[state.get_name()] = state
        if state.is_container():
            self.__containers.append(state)

    def __create_states(self, spec):
        spec_iter = spec.get_state_iter()
        for st in spec_iter.get_all_entries():
            state_name = self.gen_state_name(st)
            state = SpecStateDef(state_name, st)
            if state.get_level() > 0:
                parent_st = spec.get_parent(st)
                parent_state_name = self.gen_state_name(parent_st)
                state.set_parent_state(self.__name2state[parent_state_name])
            self.__add_state(state)

    def __create_downgrading_trs(self, spec):
        deepest = spec.get_level_count()

        if deepest < 2:
            return

        for level in range(deepest - 2, -1, -1):  # -2 = -1 -1 - Enumerated from zero and no need to build downgrading trs for deepest level
            spec_iter = spec.get_level_iter(level)
            for st in spec_iter.get_all_entries():
                state = self.__name2state[self.gen_state_name(st)]
                child_iter = spec.get_child_iter(st)
                for c_st in child_iter.get_all_entries():
                    c_state = self.__name2state[self.gen_state_name(c_st)]
                    if c_state.is_container():
                        state.add_trs_to_child_child(c_state)
                    state.add_trs_to_child(c_state)
                    if c_state.is_required():
                        break

    def __create_single_level_trs(self, spec, base=None):
        spec_iter = spec.get_hierarchical_iter(base)

        for st in spec_iter.get_all_entries():
            state = self.__name2state[self.gen_state_name(st)]
            st_next = st
            while True:
                st_next = spec_iter.get_after(st_next)
                if st_next is None:
                    break
                state_next = self.__name2state[self.gen_state_name(st_next)]
                state.add_trs_to_neighbour(state_next)
                if state_next.is_container():
                    state.add_trs_to_neighbours_childs(state_next)
                if state_next.is_required():
                    break  # No need to add anything further - we cant skip this state
            if state.is_repeated():
                state.add_trs_to_self()
            if state.is_container():
                self.__add_container_to_process(state)

    def __create_upper_level_trs(self, spec):
        self.__create_single_level_trs(spec, base=None)

    def __add_container_to_process(self, state):
        if state not in self.__containers_qq:
            self.__containers_qq.append(state)

    def __create_lower_level_trs(self, spec):
        self.__containers_qq = [c for c in self.__containers]
        while len(self.__containers_qq):
            container = self.__containers_qq[0]
            self.__containers_qq = self.__containers_qq[1:]
            st = container.get_spec()
            self.__create_single_level_trs(spec, st)

    def __eval_local_final(self, spec):
        self.__containers_qq = [c for c in self.__containers]
        while len(self.__containers_qq):
            container = self.__containers_qq[0]
            self.__containers_qq = self.__containers_qq[1:]
            st = container.get_spec()
            spec_iter = spec.get_hierarchical_iter(st)

            sts = [i for i in spec_iter.get_all_entries()]
            sts.reverse()
            for s in sts:
                state = self.__name2state[self.gen_state_name(s)]
                state.set_local_final()
                if state.is_required():
                    break

    def __create_upgrading_trs(self, spec):
        spec_iter = spec.get_state_iter()
        for st in spec_iter.get_all_entries():
            state = self.__name2state[self.gen_state_name(st)]
            if state.is_contained() and state.is_local_final():
                parent = state.get_parent_state()
                state.add_parent_trs(parent)
                while parent.is_contained() and parent.is_local_final():
                    parent = parent.get_parent_state()
                    state.add_parent_trs(parent)

    def __remove_containers(self):
        states = []
        for state in self.__states:
            if state.is_container():
                state.unlink_all()
                continue
            states.append(state)
        self.__states = states

    def __merge_transitions(self):
        for state in self.__states:
            state.merge_transitions()

    def compile(self, spec):
        spec = IterableSequenceSpec(spec)
        self.__create_states(spec)
        self.__create_downgrading_trs(spec)
        self.__create_upper_level_trs(spec)
        self.__create_lower_level_trs(spec)
        self.__eval_local_final(spec)
        self.__create_upgrading_trs(spec)
        self.__remove_containers()
        self.__merge_transitions()
        return self.__states


class SpecStateDef(object):
    def __init__(self, name, spec_dict, parent=None):
        self.__name = name
        self.__transitions = []
        self.__neighbour_transitions = []
        self.__child_transitions = []
        self.__rtransitions = []
        self.__spec_dict = spec_dict
        self.__parent = parent
        self.__is_container = spec_dict.has_key("entries")
        self.__is_contained = False
        if self.__parent:
            self.__is_contained = True
        self.__is_required = spec_dict.has_key("required") and spec_dict["required"]
        self.__is_repeatable = spec_dict.has_key("repeatable") and spec_dict["repeatable"]
        self.__is_local_final = False
        self.__is_init = spec_dict.has_key("fsm") and spec_dict["fsm"] == FsmSpecs.init
        self.__is_fini = spec_dict.has_key("fsm") and spec_dict["fsm"] == FsmSpecs.fini
        self.__uid = ue.get_uniq()

    def get_name(self):
        return self.__name

    def get_spec(self):
        return self.__spec_dict

    def get_uid(self):
        return self.__uid

    def is_init(self):
        return self.__is_init

    def is_fini(self):
        return self.__is_fini

    def is_container(self):
        return self.__is_container

    def is_contained(self):
        return self.__is_contained

    def is_local_final(self):
        return self.__is_local_final

    def is_required(self):
        return self.__is_required

    def is_repeated(self):
        return self.__is_repeatable

    def get_parent_state(self):
        return self.__parent

    def get_level(self):
        return self.__spec_dict["level"]

    def set_parent_state(self, parent):
        self.__parent = parent
        self.__is_contained = True

    def set_local_final(self):
        self.__is_local_final = True

    def add_trs_to_self(self):
        pass

    def add_trs_to_neighbour(self, to):
        if to not in self.__neighbour_transitions:
            self.__neighbour_transitions.append(to)
        to.__add_trs_from(self)

    def add_trs_to_child(self, to):
        if to not in self.__child_transitions:
            self.__child_transitions.append(to)
        to.__add_trs_from(self)

    def add_trs_to_child_child(self, child):
        for to in child.__child_transitions:
            self.add_trs_to_child(to)
            to.__add_trs_from(self)

    def add_trs_to_neighbours_childs(self, item):
        for to in item.__child_transitions:
            if to not in self.__neighbour_transitions:
                self.__neighbour_transitions.append(to)
            to.__add_trs_from(self)

    def add_parent_trs(self, parent):
        for to in parent.__neighbour_transitions:
            if to not in self.__neighbour_transitions:
                self.__neighbour_transitions.append(to)
            to.__add_trs_from(self)
        if parent.is_repeated():
            self.add_trs_to_neighbours_childs(parent)
            self.add_trs_to_neighbour(parent)

    def __add_trs_from(self, t_from):
        if t_from not in self.__rtransitions:
            self.__rtransitions.append(t_from)

    def unlink_all(self):
        for to in self.__neighbour_transitions:
            to.unlink_from(self)
        for to in self.__child_transitions:
            to.unlink_from(self)
        for t_from in self.__rtransitions:
            t_from.unlink_to(self)
        self.__neighbour_transitions = []
        self.__child_transitions = []
        self.__rtransitions = []
        self.__transitions = []

    def unlink_from(self, t_from):
        self.__rtransitions.remove(t_from)

    def unlink_to(self, to):
        if to in self.__neighbour_transitions:
            self.__neighbour_transitions.remove(to)
        if to in self.__child_transitions:
            self.__child_transitions.remove(to)
        if to in self.__transitions:
            self.__transitions.remove(to)

    def merge_transitions(self):
        self.__transitions = []
        for to in self.__neighbour_transitions:
            if to not in self.__transitions:
                self.__transitions.append(to)
        for to in self.__child_transitions:
            if to not in self.__transitions:
                self.__transitions.append(to)

    def get_transitions(self):
        return self.__transitions


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


anss = AdjNounSequenceSpec()
sc = SpecCompiler()
res = sc.compile(anss)

g = graph.SpecGraph(img_type='svg')
file_name = 'imgs/sp-{0}.svg'.format(0)
g.generate(res, file_name)
