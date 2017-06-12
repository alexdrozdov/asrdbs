#!/usr/bin/env python
# -*- #coding: utf8 -*-


import json


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def v2bool(s):
    if isinstance(s, bool):
        return s
    if isinstance(s, str):
        return s.lower() in ('true', 'yes', 'y', 't', '1')
    return bool(s)


class AppConfig(object):
    def __init__(self, filenames=None, objs=None, override_args=None):
        objs = self.__to_obj_list(filenames, objs)
        obj = self.__combine_objs(objs)
        self.__override_args(override_args, obj)
        self.__obj = obj

    def __to_obj_list(self, filenames, objs):
        assert filenames is None or objs is None
        if filenames is not None:
            objs = []
            if isinstance(filenames, str):
                filenames = [filenames, ]
            for fn in filenames:
                with open(fn) as f:
                    objs.append(json.load(f))
        if not isinstance(objs, list):
            objs = [objs, ]
        return objs

    def __combine_objs(self, objs):
        obj = objs[0]
        objs = objs[1:]
        for o in objs:
            self.__combine_obj(obj, o)
        return obj

    def __combine_obj(self, obj, o):
        pathes = self.__dict_to_pathes_values(o)
        for p, v in pathes:
            vv = self.__xpath_get(p, obj=obj)
            if vv is None:
                self.__xpath_set(p, v, obj=obj)
            elif isinstance(vv, list) and isinstance(v, list):
                vv.extend(v)
            elif isinstance(vv, list) and not isinstance(v, list):
                vv.append(v)
            else:
                raise ValueError('Couldn`t set path {0}: {1}'.format(p, v))

    def __dict_to_pathes_values(self, d):
        return list(self.__traverse_dicts('', d))

    def __traverse_dicts(self, prefix, d):
        for k, v in d.items():
            if isinstance(v, dict):
                for kk, vv in self.__traverse_dicts(prefix + '/' + k, v):
                    yield (kk, vv)
            else:
                yield (prefix + '/' + k, v)

    def __override_args(self, args, obj=None):
        for a in args:
            path, value, action = self.__parse_arg(a)
            value = self.__cast_value(path, value, obj=obj)
            if action == 'set':
                self.__xpath_set(path, value, obj=obj)
            elif action == 'append':
                self.__xpath_append(path, value, obj=obj)
            else:
                raise ValueError('Unknown action for {0}'.format(a))

    def __parse_arg(self, a):
        if '+=' in a:
            path, value = a.split('+=')
            return path, value, 'append'
        if '-=' in a:
            path, value = a.split('+=')
            return path, value, 'delete'
        if '=' in a:
            l = a.split('=')
            path = l[0]
            value = l[1] if len(l) == 2 else None
            return path, value, 'set'
        return None, None, 'none'

    def __cast_value(self, path, value, obj=None):
        v = self.__xpath_get(path, obj=obj)
        if v is None:
            print('Warning: casting to unknown value at {0}'.format(path))
            return value
        if isinstance(v, bool):
            return v2bool(value)
        if isinstance(v, int):
            return int(value)
        return value

    def exists(self, path):
        return self.__xpath_get(path) is not None

    def __xpath_get(self, path, obj=None):
        if obj is not None:
            elem = obj
        else:
            elem = self.__obj
        try:
            for x in path.strip("/").split("/"):
                try:
                    x = int(x)
                    elem = elem[x]
                except ValueError:
                    elem = elem.get(x)
        except:
            return None
        return elem

    def __xpath_append(self, path, value, obj=None):
        l = self.__xpath_get(path, obj=obj)
        if not isinstance(l, list):
            raise ValueError(
                'Couldnt append non-list {0}: {1}'.format(path, value))
        l.append(value)

    def __xpath_set(self, path, value, obj=None):
        if obj is not None:
            elem = obj
        else:
            elem = self.__obj
        path = path.strip("/").split("/")
        base_path = path[0:-1]
        last_name = path[-1]
        try:
            for x in base_path:
                try:
                    x = int(x)
                    elem = elem[x]
                except ValueError:
                    if x in elem:
                        elem = elem.get(x)
                    else:
                        elem[x] = {}
                        elem = elem[x]
            try:
                x = int(last_name)
                elem[x] = value
            except ValueError:
                elem[last_name] = value
        except:
            pass

    def __getitem__(self, i):
        return self.__xpath_get(i)

    def __setitem__(self, k, v):
        self.__xpath_set(k, v)


@singleton
class Config(AppConfig):
    pass


def configure(filenames=None, objs=None, override_args=None):
    Config(filenames=filenames, objs=objs, override_args=override_args)
