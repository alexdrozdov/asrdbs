#!/usr/bin/env python
# -*- #coding: utf8 -*-


def load_templates():
    global __all__
    import os
    import inspect
    import parser.templates.common
    mpath = os.path.dirname(os.path.realpath(__file__))
    mpath = mpath[mpath.rfind('parser'):].replace('/', '.').replace('\\', '.')
    local_path = os.path.dirname(os.path.realpath(__file__))
    __all__ = [m for m in set(
        [m.replace('.pyc', '.py').replace('.py', '')
            for m in os.listdir(local_path)]
    ) if m != '__init__' and '.' not in m]
    clss = []
    for mname in __all__:
        obj = __import__(mpath + '.' + mname, globals(), locals(), mname)
        clss.extend(
            [c[1] for c in inspect.getmembers(
                obj,
                lambda c:
                    inspect.isclass(c) and
                    c is not parser.templates.common.SpecTemplate and
                    issubclass(c, parser.templates.common.SpecTemplate)
            )]
        )
    return clss
