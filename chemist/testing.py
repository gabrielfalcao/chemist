# -*- coding: utf-8 -*-
import re


def is_valid_python_name(name):
    return re.search(r'^[a-zA-Z_][a-z_]*$', name) is not None


class Factory(object):
    def __init__(self, Model, actions=None, **defaults):
        self.Model = Model
        self.defaults = defaults
        self.actions = actions or []

    def new(self, *args, **kw):
        return self.__class__(*args, **kw)

    def clone(self, **params):
        if not params:
            params = dict(self.defaults)

        return self.new(self.Model, self.actions, **params)

    def then(self, action):
        if not callable(action):
            raise TypeError('actions must be callable, got {} ({})'.format(action, type(action)))

        self.actions.append(action)
        return self

    def with_params(self, **params):
        merged = self.defaults.copy()
        merged.update(params)
        return self.clone(**merged)

    def build(self, **params):
        # try:
        inputs = self.defaults.copy()
        inputs.update(params)
        instance = self.Model().create(**inputs)
        # except TypeError as e:
        #     import ipdb;ipdb.set_trace()
        for action in self.actions:
            result = action(instance)
            if type(result) is type(instance):
                instance = result

        return instance


class FactorySet(object):
    def __init__(self, **factory):
        self.factory = factory

    def register(self, name, Model, **defaults):
        self.validate_name(name)

        new = Factory(Model, **defaults)
        self.factory[name] = new
        return new

    def extend(self, original, name, **defaults):
        self.validate_name(name)
        ancestor = self.factory[original]
        params = ancestor.defaults.copy()
        params.update(defaults)
        new = ancestor.clone(**params)
        self.factory[name] = new
        return new

    def __getattr__(self, attr):
        try:
            return self.factory[attr]
        except (AttributeError, KeyError):
            return super(FactorySet, self).__getattribute__(attr)

    def validate_name(self, name):
        if not is_valid_python_name(name):
            # import ipdb;ipdb.set_trace()
            raise ValueError('factory names must be valid python variable names, got {}'.format(name))

        existing = self.factory.get(name, None)
        if existing:
            raise FactoryAlreadyRegistered(self, name)


class FactoryAlreadyRegistered(Exception):
    def __init__(self, factory_set, name):
        factory = factory_set.factory[name]
        tmpl = (
            "The factory set {} already "
            "has a factory named {}, "
            "registered to the model {}"
        )
        msg = tmpl.format(factory_set, name, factory.Model)
        super(FactoryAlreadyRegistered, self).__init__(msg)
