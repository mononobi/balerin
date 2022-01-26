# -*- coding: utf-8 -*-
"""
packaging base module.
"""


class Package:
    """
    package base class.

    all application python packages should be subclassed from this
    if you want to load packages respecting package dependencies.
    """

    # the name of the package.
    # example: `my_app.api`.
    # should get it from `__name__` for each package.
    NAME = None

    # list of all packages that this package is dependent
    # on them and should be loaded after all of them.
    # example: ['my_app.logging', 'my_app.api.public']
    # this can be left as an empty list if there is no dependencies.
    DEPENDS = []

    # specifies that this package is enabled and must be loaded.
    ENABLED = True

    # name of a module inside this package that should be loaded before all other modules.
    # for example: 'manager'
    # this can be left as None if there is no such file in this package needing early loading.
    COMPONENT_NAME = None

    def load_configs(self, **context):
        """
        loads all required configs of this package.

        this method could be overridden in subclasses which have configs
        to be loaded on startup.

        :keyword **context: all shared contexts which balerin is initialized with.
        """
        pass
