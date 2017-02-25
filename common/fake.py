class Named(object):
    def __init__(self, obj, name):
        self.__obj = obj
        self.__name = name

    def get_name(self):
        return self.__name

    def get(self):
        return self.__obj

    def __getattr__(self, name):
        return self.__obj.__getattribute__(name)


def named(obj, name):
    return Named(obj, name)
