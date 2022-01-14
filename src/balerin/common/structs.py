# -*- coding: utf-8 -*-
"""
common structs module.
"""

from threading import Lock
from abc import abstractmethod


class SingletonMetaBase(type):
    """
    singleton meta base class.

    this is a thread-safe implementation of singleton.
    """

    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        if cls._has_instance() is False:
            with cls._lock:
                if cls._has_instance() is False:
                    instance = super().__call__(*args, **kwargs)
                    cls._register_instance(instance)

        return cls._get_instance()

    @abstractmethod
    def _has_instance(cls):
        """
        gets a value indicating there is a registered instance.

        :raises NotImplementedError: not implemented error.

        :rtype: bool
        """

        raise NotImplementedError()

    @abstractmethod
    def _register_instance(cls, instance):
        """
        registers the given instance.

        :param object instance: instance to be registered.

        :raises NotImplementedError: not implemented error.
        """

        raise NotImplementedError()

    @abstractmethod
    def _get_instance(cls):
        """
        gets the registered instance.

        :raises NotImplementedError: not implemented error.

        :rtype: object
        """

        raise NotImplementedError()


class UniqueSingletonMeta(SingletonMetaBase):
    """
    unique singleton metaclass.

    this is a thread-safe implementation of singleton.
    this class only allows a single unique object for all descendant types.

    for example: {Base -> UniqueSingletonMeta, A -> Base, B -> A}
    if some_object = Base() then always Base() = A() = B() = some_object.
    or if some_object = A() then always A() = B() = some_object != Base().
    """

    _instance = None
    _lock = Lock()

    def _has_instance(cls):
        """
        gets a value indicating that there is a registered instance.

        :rtype: bool
        """

        return cls._instance is not None

    def _register_instance(cls, instance):
        """
        registers the given instance.
        """

        cls._instance = instance

    def _get_instance(cls):
        """
        gets the registered instance.

        :rtype: object
        """

        return cls._instance


class MultiSingletonMeta(SingletonMetaBase):
    """
    multi singleton metaclass.

    this is a thread-safe implementation of singleton.
    this class allows a unique object per each type of descendants.

    for example: {Base -> UniqueSingletonMeta, A -> Base, B -> A}
    if some_object = Base() then always Base() != A() != B() but always Base() = some_object.
    or if some_object = A() then always Base() != A() != B() but always A() = some_object.
    """

    # a dictionary containing an instance of each type.
    # in the form of: {type: instance}
    _instances = dict()
    _lock = Lock()

    def _has_instance(cls):
        """
        gets a value indicating that there is a registered instance.

        :rtype: bool
        """

        return cls in cls._instances

    def _register_instance(cls, instance):
        """
        registers the given instance.
        """

        cls._instances[cls] = instance

    def _get_instance(cls):
        """
        gets the registered instance.

        :rtype: object
        """

        return cls._instances.get(cls)


class HookSingletonMeta(MultiSingletonMeta):
    """
    hook singleton metaclass.

    this is a thread-safe implementation of singleton.
    """

    _instances = dict()
    _lock = Lock()


class Hook(metaclass=HookSingletonMeta):
    """
    base hook class.

    all packaging hook classes must be subclassed from this one.
    """
    pass


class ManagerSingletonMeta(MultiSingletonMeta):
    """
    manager singleton metaclass.

    this is a thread-safe implementation of singleton.
    """

    _instances = dict()
    _lock = Lock()
