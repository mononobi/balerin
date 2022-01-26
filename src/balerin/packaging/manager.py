# -*- coding: utf-8 -*-
"""
packaging manager module.
"""

import os
import inspect

from time import time
from pathlib import Path
from threading import Lock
from importlib import import_module
from collections import OrderedDict

import balerin.common.utils as utils

from balerin.packaging.base import Package
from balerin.common.mixin import HookMixin
from balerin.common.structs import ManagerSingletonMeta
from balerin.packaging.hooks import PackagingHookBase
from balerin.packaging.exceptions import InvalidPackageNameError, \
    ComponentModuleNotFoundError, InvalidPackagingHookTypeError, \
    CircularDependencyDetectedError, PackageNotExistedError, \
    PackageIsIgnoredError, PackageIsDisabledError, SelfDependencyDetectedError, \
    SubPackageDependencyDetectedError, InvalidRootPathError


class PackagingManager(HookMixin, metaclass=ManagerSingletonMeta):
    """
    packaging manager class.
    """

    _lock = Lock()
    hook_type = PackagingHookBase
    invalid_hook_type_error = InvalidPackagingHookTypeError

    def __init__(self, *root, **options):
        """
        creates a new instance of PackagingManager.

        :param str root: the absolute path of application root package.
                         it can be a single path or a list of paths
                         to be loaded respectively.

        :keyword str base_component: specifies a module name which must be loaded before all
                                     other modules in each package if available.
                                     for example `manager`. this value could be overridden
                                     in each `Package` class using `COMPONENT_NAME` attribute.

        :keyword bool verbose: specifies that loading info should be printed on each step.
                               defaults to True if not provided.

        :keyword list[str] ignored_packages: list of package names that must be
                                             ignored from loading. package names
                                             must be fully qualified.
                                             for example: `my_app.api.public`.
                                             notice that if a package that has sub-packages
                                             added to ignore list, all of its sub-packages will
                                             be ignored automatically even if not present in
                                             ignore list.

        :keyword list[str] ignored_modules: list of module names that must be ignored
                                            from loading. module names could be fully
                                            qualified or just the module name itself.
                                            for example:
                                            `my_app.api.enumerations` or `enumerations`.
                                            notice that if only module name is provided,
                                            then all modules matching the provided name will
                                            be ignored from loading.

        :keyword function ignored_detector: a function to be used to detect if a
                                            package or module should be ignored.
                                            it must take two arguments, the first
                                            is the fully qualified name and the second
                                            is a boolean value indicating that the input
                                            is a module. it also should take optional keyword
                                            arguments as context. it should return
                                            a boolean value. for example:
                                            `my_detector(name, is_module, **context)`

        :keyword function module_loader: a function to be used to load custom
                                         attributes of a module. it should take
                                         two arguments, a name and a module instance.
                                         it also should take optional keyword arguments
                                         as context. the output will be ignored. for example:
                                         `my_loader(name, module, **context)`

        :keyword dict context: a dict containing all shared contexts to
                               be used for example inside `ignored_detector`
                               and `module_loader` functions.

        :raises InvalidRootPathError: invalid root path error.
        """

        super().__init__()

        # this flag indicates that application has been loaded.
        # it is required for environments in which server starts
        # multiple threads before application gets loaded.
        self._is_loaded = False

        # holds the names of all application packages that should be loaded.
        self._all_packages = []

        # holds the name of loaded packages.
        self._loaded_packages = []

        # holds the name of disabled packages.
        self._disabled_packages = []

        # holds all root paths that must be loaded respectively.
        self._roots = root

        for item in self._roots:
            if not os.path.isdir(item):
                raise InvalidRootPathError('Provided root path [{root}] '
                                           'is invalid.'.format(root=item))

        # holds the module name that should be loaded before
        # all other modules inside each package.
        self._base_component = options.get('base_component')

        # holds a function to be used to detect if a package or module should be ignored.
        self._ignored_detector = options.get('ignored_detector')

        # holds a function to be used to load custom attributes of a module.
        self._module_loader = options.get('module_loader')

        # a dict containing all shared contexts to be used for example
        # inside `ignored_detector` and `module_loader` functions.
        self._context = options.get('context') or {}

        # a dict containing each package name and all of its dependency package names.
        # in the form of:
        # {str package_name: list[str dependency_package_name]}
        self._dependency_map = dict()

        # holds the full path of directories that are not a package (not having __init__.py)
        self._not_packages = []

        self._ignored_packages = utils.make_iterable(options.get('ignored_packages'))
        self._ignored_modules = utils.make_iterable(options.get('ignored_modules'))

        # specifies that loading info must be printed on each step.
        self._verbose = options.get('verbose', True)

        # this will keep all loaded components for different roots inside it.
        # in the form of: dict[str root: dict[str package_name: list[str] modules]]
        self._components = OrderedDict()

    def load_components(self, **options):
        """
        loads required packages and modules for application startup.

        :raises PackageIsIgnoredError: package is ignored error.
        :raises PackageIsDisabledError: package is disabled error.
        :raises PackageNotExistedError: package not existed error.
        :raises SelfDependencyDetectedError: self dependency detected error.
        :raises SubPackageDependencyDetectedError: sub-package dependency detected error.
        :raises CircularDependencyDetectedError: circular dependency detected error.
        :raises PackageExternalDependencyError: package external dependency error.
        """

        if self._is_loaded is True:
            return

        with self._lock:
            if self._is_loaded is True:
                return

            start_time = time()
            self._initialize()

            if self._verbose:
                print('Loading application components...')

            for root in self._roots:
                exclude = [item for item in self._roots if item != root]
                self._find_loadable_components(root, exclude, **options)

            for root, components in self._components.items():
                self._load_components(components, **options)

            self._after_packages_loaded()
            self._is_loaded = True

            if self._verbose:
                print('Total of [{count}] packages loaded.'
                      .format(count=len(self._loaded_packages)))

                end_time = time()
                duration = '{:0.1f}'.format((end_time - start_time) * 1000)
                print('Application loaded in [{duration}] milliseconds.'
                      .format(duration=duration))

    def load(self, module_name, **options):
        """
        loads the specified module.

        :param str module_name: full module name.
                                example module_name = `my_app.application.decorators`.

        :rtype: Module
        """

        module = import_module(module_name)
        return module

    def get_loaded_packages(self):
        """
        gets the name of all loaded packages.

        :rtype: list[str]
        """

        return list(self._loaded_packages)

    def is_package_loaded(self, name):
        """
        gets a value indicating that given package is loaded.

        :param str name: package fully qualified name.

        :rtype: bool
        """

        return name in self._loaded_packages

    def get_context(self):
        """
        gets a dict of all shared contexts.

        :rtype: dict
        """

        return dict(**self._context)

    def _initialize(self):
        """
        initializes required data.
        """

        self._disabled_packages.clear()
        self._not_packages.clear()
        self._dependency_map.clear()
        self._all_packages.clear()
        self._loaded_packages.clear()
        self._components.clear()

    def _after_packages_loaded(self):
        """
        this method will call `after_packages_loaded` method of all registered hooks.
        """

        for hook in self._get_hooks():
            hook.after_packages_loaded()

    def _package_loaded(self, package_name, **options):
        """
        this method will call `package_loaded` method of all registered hooks.

        :param str package_name: name of the loaded package.
        """

        for hook in self._get_hooks():
            hook.package_loaded(package_name, **options)

    def _load_component(self, package_name, module_names, component_name, **options):
        """
        loads the given component.

        :param str package_name: full package name to be loaded.
        :param list[str] module_names: full module names to be loaded.
        :param str component_name: component name of this package.

        :raises ComponentModuleNotFoundError: component module not found error.
        """

        self.load(package_name)

        # component module should be loaded first if available.
        component_module = None
        force_component = True
        if component_name is None:
            component_name = self._base_component
            force_component = False

        if component_name is not None:
            component_module = self._merge_module_name(package_name, component_name)

        if component_module is not None and component_module in module_names:
            module = self.load(component_module, **options)
            self._custom_load_module(component_module, module)
        elif component_module is not None and component_module not in module_names \
                and force_component is True:
            raise ComponentModuleNotFoundError('Component module [{name}] not '
                                               'found in [{package}] package.'
                                               .format(name=component_module,
                                                       package=package_name))

        for name in module_names:
            if name != component_module:
                module = self.load(name, **options)
                self._custom_load_module(name, module)

        self._loaded_packages.append(package_name)
        self._package_loaded(package_name, **options)

        if self._verbose:
            print('[{package}] package loaded. including [{module_count}] modules.'
                  .format(package=package_name, module_count=len(module_names)))

    def _load_components(self, components, **options):
        """
        loads the given components considering their dependency on each other.

        :param dict components: full package names and their
                                modules to be loaded.

        :note components: dict[str package_name: list[str] modules]

        :raises PackageIsIgnoredError: package is ignored error.
        :raises PackageIsDisabledError: package is disabled error.
        :raises PackageNotExistedError: package not existed error.
        :raises SelfDependencyDetectedError: self dependency detected error.
        :raises SubPackageDependencyDetectedError: sub-package dependency detected error.
        :raises CircularDependencyDetectedError: circular dependency detected error.
        :raises PackageExternalDependencyError: package external dependency error.
        """

        # a dictionary containing all dependent package names and their respective modules.
        # in the form of {str package_name: [str module]}.
        dependent_components = dict()

        for package in components:
            dependencies = []
            package_class = self._get_package_class(package)
            if package_class is not None:
                dependencies = package_class.DEPENDS

            self._validate_dependencies(package, dependencies)

            # checking whether this package has any dependencies.
            # if so, check those dependencies have been loaded or not.
            # if not, then put this package into dependent_packages and
            # load it later. otherwise, load it now.
            if (len(dependencies) <= 0 or
                self._is_dependencies_loaded(dependencies) is True) and \
                    self._is_parent_loaded(package) is True:

                instance = None
                if package_class is not None:
                    instance = package_class()
                    instance.load_configs(**self._context)

                component_name = None
                if instance is not None:
                    component_name = instance.COMPONENT_NAME
                self._load_component(package, components[package], component_name, **options)
            else:
                dependent_components[package] = components[package]

        # now, go through dependent components if any, and try to load them.
        if len(dependent_components) > 0:
            self._load_components(dependent_components, **options)

    def _validate_dependencies(self, package_name, dependencies):
        """
        validates that given package's dependencies have no problem.

        it checks for different problems such as self and circular
        dependencies, unavailable dependencies, external dependencies and more.

        it raises an error if a problem has been detected.
        for example, if `my_app.database` has a dependency on `my_app.logging`
        and `my_app.logging` also has a dependency on `my_app.database`, this
        method raises an error.

        :param str package_name: package name.
        :param list[str] dependencies: list of given package's dependencies.

        :raises PackageIsIgnoredError: package is ignored error.
        :raises PackageIsDisabledError: package is disabled error.
        :raises PackageNotExistedError: package not existed error.
        :raises SelfDependencyDetectedError: self dependency detected error.
        :raises SubPackageDependencyDetectedError: sub-package dependency detected error.
        :raises CircularDependencyDetectedError: circular dependency detected error.
        """

        dependencies = utils.make_iterable(dependencies, list)
        self._check_dependencies_exist(package_name, dependencies)

        self._dependency_map[package_name] = dependencies
        if len(dependencies) <= 0:
            return

        if package_name in dependencies:
            raise SelfDependencyDetectedError('Package [{source}] has a dependency on itself. '
                                              'it is a mistake to depend a package on itself.'
                                              .format(source=package_name))

        for item in dependencies:
            if self._contains(package_name, item) is True:
                raise SubPackageDependencyDetectedError('Package [{root}] has a dependency on '
                                                        'its sub-package [{child}]. it is a '
                                                        'mistake to depend a package on its '
                                                        'own sub-packages.'
                                                        .format(root=package_name, child=item))

            reverse_dependencies = self._dependency_map.get(item)
            if reverse_dependencies is not None:
                if package_name in reverse_dependencies:
                    raise CircularDependencyDetectedError('There is a circular dependency '
                                                          'between [{source}] and [{reverse}] '
                                                          'packages.'
                                                          .format(source=package_name,
                                                                  reverse=item))

    def _check_dependencies_exist(self, package_name, dependencies):
        """
        checks that given dependency packages are available in the application scope.

        :param str package_name: package name.
        :param list[str] dependencies: list of given package's dependencies.

        :raises PackageIsIgnoredError: package is ignored error.
        :raises PackageIsDisabledError: package is disabled error.
        :raises PackageNotExistedError: package not existed error.
        """

        if dependencies is None:
            return

        for item in dependencies:
            if item not in self._all_packages:
                base_message = 'Provided dependency package [{name}] ' \
                               'specified in [{source}] package,' \
                    .format(name=item, source=package_name)

                if self._is_ignored_package(item):
                    raise PackageIsIgnoredError('{base_message} is ignored in '
                                                'packaging config store.'
                                                .format(base_message=base_message))
                if self._is_disabled_package(item):
                    raise PackageIsDisabledError('{base_message} is disabled.'
                                                 .format(base_message=base_message))

                raise PackageNotExistedError('{base_message} does not exist.'
                                             .format(base_message=base_message))

    def _is_detected_ignored(self, name, is_module):
        """
        gets a value indicating that the input package or module should be ignored.

        :param str name: fully qualified name of the package or module.
        :param bool is_module: a value indicating that given input is a module.

        :rtype: bool
        """

        if self._ignored_detector is not None:
            return self._ignored_detector(name, is_module, **self._context)

        return False

    def _custom_load_module(self, name, module):
        """
        loads the custom attributes of the given module.

        :param str name: fully qualified name of the module.
        :param Module module: module instance.
        """

        if self._module_loader is not None:
            self._module_loader(name, module, **self._context)

    def _find_loadable_components(self, root_path, exclude=None, **options):
        """
        finds all package and module names that should be loaded included in given root path.

        :param str root_path: root path to look for components inside it.

        :param str | list[str] exclude: specifies full paths inside the
                                        root path to ignore them. otherwise,
                                        it loops in all available paths.
        """

        single_root = root_path
        include = utils.make_iterable(root_path, list)
        exclude = utils.make_iterable(exclude, list)
        path = Path(root_path)
        root_path = path.parent.absolute().as_posix()

        for root, directories, file_names in os.walk(root_path, followlinks=True):
            temp_dirs = list(directories)
            for single_dir in temp_dirs:
                visiting_path = os.path.abspath(os.path.join(root, single_dir))
                if self._should_visit(include, exclude, visiting_path) is False:
                    directories.remove(single_dir)

            for directory in directories:
                combined_path = os.path.join(root, directory)

                if not self._is_package(combined_path):
                    continue

                package_name = self._get_package_name(combined_path, root_path)
                if self._is_ignored_package(package_name):
                    continue

                package_class = self._get_package_class(package_name)
                if package_class is not None and package_class.ENABLED is False:
                    self._disabled_packages.append(package_name)
                    continue

                if self._is_disabled_package(package_name):
                    continue

                self._all_packages.append(package_name)
                components = self._components.setdefault(single_root, {})
                components.setdefault(package_name, [])

                files = os.listdir(combined_path)
                for file_name in files:
                    if not self._is_module(file_name):
                        continue

                    module_name = file_name.replace('.py', '')
                    full_module_name = self._get_module_name(package_name, module_name)
                    if self._is_ignored_module(full_module_name):
                        continue

                    components[package_name].append(full_module_name)

    def _is_included(self, include, visiting_path):
        """
        returns a value indicating that the given visiting path is under include path.

        :param list[str] include: full directory names inside the
                                  root path to just loop inside those.
                                  otherwise, it loops in all available
                                  directories.

        :param str visiting_path: full path which must be checked for inclusion.

        :rtype: bool
        """

        if include is None or len(include) <= 0:
            return True

        for path in include:
            if visiting_path.startswith(path):
                return True

        return False

    def _is_excluded(self, exclude, visiting_path):
        """
        returns a value indicating that the given visiting path is under exclude path.

        :param list[str] exclude: full directory names inside the
                                  root path to ignore them. otherwise,
                                  it loops in all available directories.

        :param str visiting_path: full path which must be checked for exclusion.

        :rtype: bool
        """

        if exclude is None or len(exclude) <= 0:
            return False

        for path in exclude:
            if visiting_path.startswith(path):
                return True

        return False

    def _should_visit(self, include, exclude, visiting_path):
        """
        gets a value indicating that given path should be visited.

        :param list[str] include: full directory names inside the
                                  root path to just loop inside those.
                                  otherwise, it loops in all available
                                  directories.

        :param list[str] exclude: full directory names inside the
                                  root path to ignore them. otherwise,
                                  it loops in all available directories.

        :param str visiting_path: full path which must be checked for exclusion.

        :rtype: bool
        """

        return self._is_included(include, visiting_path) is True and \
            self._is_excluded(exclude, visiting_path) is False

    def _is_equal(self, condition, full_module_or_package):
        """
        gets a value indicating that given name is equal with given condition.

        :param str condition: condition to compare with name.
                              for example: `*.database`, then all values
                              that have database in their second part
                              and their parts count are equal to or greater
                              than condition parts count will be recognized as equal.

        :param str full_module_or_package: module or package name to be compared.
                                           for example: `my_app.database`.

        :rtype: bool
        """

        condition_parts = condition.split('.')
        full_module_or_package_parts = full_module_or_package.split('.')

        if len(condition_parts) > len(full_module_or_package_parts):
            return False

        for index, item in enumerate(condition_parts):
            if item != '*' and item != full_module_or_package_parts[index]:
                return False

        return True

    def _is_disabled_package(self, package_name):
        """
        gets a value indicating that given package should be considered as disabled.

        it will be detected based on parent packages of this package.

        :param str package_name: full package name.
                                 example package_name = `my_app.database`.

        :rtype: bool
        """

        for disabled in self._disabled_packages:
            if package_name.startswith(disabled) or self._is_equal(disabled, package_name):
                return True

        return False

    def _is_ignored_package(self, package_name):
        """
        gets a value indicating that given package should be ignored.

        :param str package_name: full package name.
                                 example package_name = `my_app.database`.

        :rtype: bool
        """

        for ignored in self._ignored_packages:
            if package_name.startswith(ignored) or self._is_equal(ignored, package_name):
                return True

        return self._is_detected_ignored(package_name, is_module=False)

    def _is_ignored_module(self, module_name):
        """
        gets a value indicating that given module should be ignored.

        :param str module_name: full module name.
                                example module_name = `my_app.api.error_handlers`.

        :rtype: bool
        """

        for ignored in self._ignored_modules:
            if module_name.endswith(ignored):
                return True

        return self._is_detected_ignored(module_name, is_module=True)

    def _contains(self, root, component_name):
        """
        gets a value indicating that given component
        qualified name belongs to the provided root.

        :param str root: root name that should be checked for component existence.
                         example root = `application.custom`

        :param str component_name: component name that should be
                                   checked for existence in root.
                                   example component_name = `application.custom.api`

        :rtype: bool
        """

        parts_component = component_name.split('.')
        parts_root = root.split('.')
        if len(parts_component) < len(parts_root):
            return False

        component_root = '.'.join(parts_component[0:len(parts_root)])

        return component_root == root

    def _get_package_name(self, path, root_path):
        """
        gets the full package name for provided path.

        :param str path: full path of package.
                         example path = `/home/src/my_app/database`.

        :param str root_path: root path in which this path is located.
                              example root_path = `/home/src`

        :rtype: str
        """

        return utils.get_package_name(path, root_path)

    def _merge_module_name(self, package_name, component_name):
        """
        merges package and component name and gets the fully qualified module name.

        :param str package_name: package name.
                                 example package_name = `my_app.database`.

        :param str component_name: component name.
                                   example component_name = `database.component`.

        :rtype: str
        """

        parts = component_name.split('.')
        return self._get_module_name(package_name, parts[-1])

    def _get_module_name(self, package_name, module_name):
        """
        gets the full module name.

        :param str package_name: package name.
                                 example package_name = `my_app.database`.

        :param str module_name: module name.
                                example module_name = `api`.

        :rtype: str
        """

        return '{package}.{module}'.format(package=package_name, module=module_name)

    def _is_package(self, path):
        """
        gets a value indicating that given path belongs to a python package.

        it simply checks that `__init__` module exists or not.

        :param str path: full path of package.
                         example path = `/home/src/my_app/database`.

        :rtype: bool
        """

        is_package = self._has_module(path, '__init__')
        if is_package is False:
            self._not_packages.append(path)

        return is_package and self._parent_is_package(path)

    def _parent_is_package(self, path):
        """
        gets a value indicating that the parent of given path is a python package.

        :param str path: full path of package.
                         example path = `/home/src/my_app/database`.

        :rtype: bool
        """

        for not_package in self._not_packages:
            if path.startswith(not_package):
                return False

        return True

    def _is_module(self, file_name):
        """
        gets a value indicating that given file is a standalone python module.

        excluding `__init__` module which belongs to package.
        it simply checks that file name ends with '.py' and not being `__init__.py`.

        :param str file_name: file name.
                              example file_name = `services.py`
        :rtype: bool
        """

        return file_name.endswith('.py') and '__init__.py' not in file_name

    def _has_module(self, path, module_name):
        """
        gets a value indicating that given module exists in specified path.

        :param str path: path to check module availability in it.
                         example path = `/home/src/my_app/database`.

        :param str module_name: module name.
                                example module_name = `__init__`.

        :rtype: bool
        """

        return os.path.isfile(os.path.join(path, '{module}.py'.format(module=module_name)))

    def _get_package_class(self, package_name):
        """
        gets the package class implemented in given package if available, otherwise returns None.

        :param str package_name: full package name.
                                 example package_name = `my_app.api`.

        :rtype: type
        """

        module = self.load(package_name)
        package_class = None

        for cls in module.__dict__.values():
            if inspect.isclass(cls) and cls is not Package and issubclass(cls, Package):
                package_class = cls
        return package_class

    def _is_dependencies_loaded(self, dependencies):
        """
        gets a value indicating that given dependencies has been already loaded.

        :param list[str] dependencies: full dependency names.
                                       example dependencies = `my_app.logging`

        :rtype: bool
        """

        for dependency in dependencies:
            if dependency not in self._loaded_packages:
                return False

        return True

    def _is_parent_loaded(self, package_name):
        """
        gets a value indicating that given package's parent package has been loaded.

        :param str package_name: full package name.
                                 example package_name = `my_app.encryption.handlers`

        :raises InvalidPackageNameError: invalid package name error.

        :rtype: bool
        """

        items = package_name.split('.')
        parent_package = None

        length = len(items)
        if length == 1:
            parent_package = items[0]
        elif length > 1:
            parent_package = '.'.join(items[:-1])
        else:
            raise InvalidPackageNameError('Input package name [{package_name}] is invalid.'
                                          .format(package_name=package_name))

        # application root packages have no parent, so it
        # should always return `True` for them.
        if parent_package == package_name:
            return True

        return self._is_dependencies_loaded([parent_package])
