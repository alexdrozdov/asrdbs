import os


mpath = os.path.dirname(os.path.realpath(__file__))
mpath = mpath[mpath.rfind('parser'):].replace('/', '.').replace('\\', '.')
local_path = os.path.dirname(os.path.realpath(__file__))
__all__ = [m for m in set(
    [m.replace('.pyc', '.py').replace('.py', '')
        for m in os.listdir(local_path)]
) if m != '__init__' and '.' not in m]
for mname in __all__:
    obj = __import__(mpath + '.' + mname, globals(), locals(), mname)
