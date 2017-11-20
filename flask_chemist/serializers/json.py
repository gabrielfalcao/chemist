# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import json
import logging
from datetime import date, time, datetime


logger = logging.getLogger(__name__)


def json_converter(value):
    date_types = (datetime, date, time)
    if isinstance(value, date_types):
        value = value.isoformat()

    return str(value)


def dumps(data, **kw):
    kw['default'] = json_converter
    return json.dumps(data, **kw)


def loads(*args, **kw):
    try:
        return json.loads(*args, **kw)

    except (ValueError, TypeError) as e:
        logger.warning('json.loads() defaulting to empty object due to failure to load json: {}'.format(e))
        return {}
