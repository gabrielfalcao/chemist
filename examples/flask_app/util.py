# -*- coding: utf-8 -*-


def any_of(*items):
    """simple algorithm to return the first of the given values that resolves to a positive boolean
    """
    for item in items:
        if bool(item):
            return item
