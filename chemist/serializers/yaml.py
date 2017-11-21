# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import yaml
import dateutil.parser

from datetime import date, time, datetime


class YamlDumper(yaml.Dumper):
    def resolve(self, kind, value, implicit):
        try:
            return super(YamlDumper, self).resolve(kind, value, implicit)
        except:
            datetime_types = (datetime, date, time)
            if isinstance(value, datetime_types):
                value = value.isoformat()
            else:
                value = repr(value)

        return str(value)


class YamlLoader(yaml.Loader):
    def resolve(self, kind, value, implicit):
        try:
            return dateutil.parser.parse(value)
        except:
            return super(YamlLoader, self).resolve(kind, value, implicit)


def dumps(data, **kw):
    kw['Dumper'] = YamlDumper
    kw['default_flow_style'] = False
    return yaml.dump(data, **kw)


def loads(*args, **kw):
    kw['Loader'] = YamlLoader
    return yaml.load(*args, **kw)
