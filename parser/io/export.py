import collections
import common.config
import common.output
import parser.io.fmtconvert


class Export(object):
    def generate(self, cfg_path, **kwargs):
        cfg = common.config.Config()
        for group_name, group in cfg[cfg_path].items():
            if group_name not in kwargs:
                continue
            itr = kwargs[group_name]
            self.__generate_group(group_name, group, itr)

    def __generate_group(self, name, group, itr):
        itr = list(itr)
        tgt_dir = group['path']
        flt = group.get('filter')
        fmts = collections.OrderedDict(
            str={'fmt': 'str', 'save-to-file': False},
            json={'fmt': 'json', 'save-to-file': True, 'extension': '.json'},
            svg={'fmt': 'svg', 'save-to-file': True, 'extension': '.svg'},
        )
        for fmt in (i for i in fmts if i in group and group[i]):
            self.__generate_fmt(
                itr=itr,
                fmt_info=fmts[fmt],
                tgt_dir=tgt_dir,
                flt=flt
            )

    def __generate_fmt(self, itr, fmt_info, tgt_dir, flt):
        for e in itr:
            name = e.get_name()
            if flt is not None and name not in flt:
                continue
            try:
                data = e.format(fmt_info['fmt'])
            except:
                data = parser.io.fmtconvert.convert(
                    e.format('dict'),
                    'dict', fmt_info['fmt']
                )
            if fmt_info['save-to-file']:
                file_name = common.output.output.get_output_file(
                    tgt_dir,
                    '{0}{1}'.format(name, fmt_info['extension'])
                )
                with open(file_name, 'w') as f:
                    f.write(data)
            else:
                print(data)


def generate(cfg_path, **kwargs):
    g = Export()
    g.generate(cfg_path, **kwargs)
