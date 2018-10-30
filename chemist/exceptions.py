# -*- coding: utf-8 -*-

class FieldTypeValueError(Exception):
    def __init__(self, model, attr, e):
        msg = "{}.{} value type error: {}".format(model, attr, e)
        super(FieldTypeValueError, self).__init__(msg)


class MultipleEnginesSpecified(Exception):
    pass


class EngineNotSpecified(Exception):
    pass


class InvalidColumnName(Exception):
    pass


class InvalidQueryModifier(Exception):
    pass


class InvalidModelDeclaration(Exception):
    pass


class RecordNotFound(Exception):
    pass
