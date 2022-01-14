# -*- coding: utf-8 -*-
"""
common utils module.
"""

import os
import sys


def make_iterable(values, collection=None):
    """
    converts the provided values to iterable.

    it returns a collection of values using the given collection type.

    :param object | list[object] | tuple[object] | set[object] values: value or values to make
                                                                       iterable. if the values
                                                                       are iterable, it just
                                                                       converts the collection
                                                                       to given type.

    :param type[list | tuple | set] collection: collection type to use.
                                                defaults to list if not provided.

    :rtype: list | tuple | set
    """

    if collection is None:
        collection = list

    if values is None:
        return collection()

    if not isinstance(values, (list, tuple, set)):
        values = (values,)

    return collection(values)


def try_get_fully_qualified_name(some_object):
    """
    tries to get the fully qualified name of given object.

    it tries to return `__module__.__name__` for given object.
    for example: `my_app.api.services.create_route`.
    but if it fails to get any of those, it returns the `__str__` for that object.

    :param object some_object: object to get its fully qualified name.

    :rtype: str
    """

    module = None
    name = None
    try:
        module = some_object.__module__
        if module == '' or module.isspace():
            module = None
    except AttributeError:
        module = None

    try:
        name = some_object.__name__
        if name == '' or name.isspace():
            name = None
    except AttributeError:
        name = None

    if module is not None and name is not None:
        return '{module}.{name}'.format(module=module, name=name)

    return str(some_object)


def get_module_file_path(module_name):
    """
    gets the absolute file path of module with given name.

    :param str module_name: module name to get its file path.

    :rtype: str
    """

    return os.path.abspath(sys.modules[module_name].__file__)


def get_main_package_name(module_name):
    """
    gets the main package name from given module name.

    for example for `my_app.database.manager` module, it
    returns `my_app` as the main package name.

    :param str module_name: module name to get its root package name.

    :rtype: str
    """

    return module_name.split('.')[0]


def get_main_package_path(module_name):
    """
    gets the absolute path of the main package of module with given name.

    :param str module_name: module name to get its main package path.

    :rtype: str
    """

    relative_module_path = module_name.replace('.', os.path.sep)
    root_package = get_main_package_name(module_name)
    absolute_module_path = get_module_file_path(module_name)
    temp_absolute_module_path = absolute_module_path.replace(relative_module_path, '*')
    excess_part = temp_absolute_module_path.split('*')[-1]
    list_path = list(temp_absolute_module_path)

    for i in range(-1, -len(list_path), -1):
        if list_path[i] == '*':
            list_path[i] = root_package
            break

    main_package_path = ''.join(list_path)
    main_package_path = main_package_path.replace('*', relative_module_path)
    main_package_path = main_package_path.replace(excess_part, '').rstrip(os.path.sep)

    return main_package_path


def get_package_name(path, root_path):
    """
    gets the full package name for provided path.

    :param str path: full path of package.
                     example path = `/home/src/my_app/database`.

    :param str root_path: root path in which this path is located.
                          example root_path = `/home/src`

    :rtype: str
    """

    return path.replace(root_path, '').replace(os.path.sep, '.').lstrip('.')
