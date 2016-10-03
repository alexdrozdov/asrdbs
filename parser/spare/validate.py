class ValidatePresence(object):
    def __init__(self, spec, required_names):
        self.__spec_name = spec.get_name()
        self.__required_names = [self.__resolve_name(name) for name in required_names]

    def __resolve_name(self, name):
        if '$SPEC' in name:
            return name.replace('$SPEC', '::' + self.__spec_name)
        return name

    def validate(self, sequence):
        for name in self.__required_names:
            if not sequence.has_item(starts_with=name):
                return False
        return True


class ValidateAll(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        for v in self.__validators:
            if not v.validate(sequence):
                return False
        return True


class ValidateAny(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        for v in self.__validators:
            if v.validate(sequence):
                return True
        return False


class ValidateNone(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        for v in self.__validators:
            if v.validate(sequence):
                return False
        return True


class ValidateOne(object):
    def __init__(self, validators):
        self.__validators = validators[:]

    def validate(self, sequence):
        r = False
        for v in self.__validators:
            if v.validate(sequence):
                if r:
                    return False
                r = True
        return r
