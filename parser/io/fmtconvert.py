import os
import json
import jinja2
import subprocess
import common.config


class Convertor(object):
    def __init__(self, from_fmt, to_fmt):
        Convertor.register(self, from_fmt, to_fmt)

    @classmethod
    def register(cls, convertor, from_fmt, to_fmt):
        if not hasattr(cls, 'fromto'):
            cls.fromto = {}
        if from_fmt not in cls.fromto:
            cls.fromto[from_fmt] = {}
        cls.fromto[from_fmt][to_fmt] = convertor

    @classmethod
    def get(cls, f, t):
        return cls.fromto[f][t]

    def __call__(self, obj):
        raise RuntimeError('not implemented')


class DictToJson(Convertor):
    def __init__(self):
        super().__init__(from_fmt='dict', to_fmt='json')

    def __call__(self, obj):
        return json.dumps(obj)


class DictToSvg(Convertor):
    def __init__(self):
        super().__init__(from_fmt='dict', to_fmt='svg')
        self.__load_templates()
        self.__load_styles()
        self.__load_fmtmaps()

    def __load_templates(self):
        cfg = common.config.Config()
        dirs = cfg['parser/io/jinja2/templates']
        self.__env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(dirs)
        )

    def __load_styles(self):
        self.__styles = {}
        cfg = common.config.Config()
        d = cfg['parser/io/jinja2/styles']
        for f in [fname for fname in os.listdir(d) if fname.endswith('.json')]:
            with open(os.path.join(d, f)) as fd:
                j = json.load(fd)
                self.__styles[j['name']] = j['style']

    def __load_fmtmaps(self):
        cfg = common.config.Config()
        self.__fmtmap = cfg['parser/io/jinja2/fmtmap']

    def __to_dot(self, obj):
        fmt = obj.get('__fmt_hint')
        if fmt is None:
            raise RuntimeError('object doesnt contain format hint')

        tmpl_name = self.__fmtmap.get(fmt)
        if tmpl_name is None:
            raise RuntimeError('jinja2 format {0} unknown'.format(fmt))

        style = obj.get('__style_hint')
        styles = None
        if style is not None:
            styles = self.__styles.get(style)

        template = self.__env.get_template(tmpl_name)
        return template.render(g=obj, styles=styles)

    def __call__(self, obj):
        dot_data = self.__to_dot(obj)
        p = subprocess.Popen(
            ['dot', '-T', 'svg'],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return p.communicate(input=dot_data.encode())[0].decode()


convertors = []


def convert(obj, from_fmt, to_fmt):
    global convertors
    if not convertors:
        convertors = [DictToJson(), DictToSvg()]
    return Convertor.get(from_fmt, to_fmt)(obj)
