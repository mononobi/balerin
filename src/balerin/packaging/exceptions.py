# -*- coding: utf-8 -*-
"""
packaging exceptions module.
"""

from balerin.common.exceptions import BalerinException


class PackagingManagerException(BalerinException):
    """
    packaging manager exception.
    """
    pass


class InvalidPackageNameError(PackagingManagerException):
    """
    invalid package name error.
    """
    pass


class ComponentModuleNotFoundError(PackagingManagerException):
    """
    component module not found error.
    """
    pass


class InvalidRootPathError(PackagingManagerException):
    """
    invalid root path error.
    """
    pass


class InvalidPackagingHookTypeError(PackagingManagerException):
    """
    invalid packaging hook type error.
    """
    pass


class CircularDependencyDetectedError(PackagingManagerException):
    """
    circular dependency detected error.
    """
    pass


class SelfDependencyDetectedError(PackagingManagerException):
    """
    self dependency detected error.
    """
    pass


class SubPackageDependencyDetectedError(PackagingManagerException):
    """
    sub-package dependency detected error.
    """
    pass


class PackageNotExistedError(PackagingManagerException):
    """
    package not existed error.
    """
    pass


class PackageIsIgnoredError(PackagingManagerException):
    """
    package is ignored error.
    """
    pass


class PackageIsDisabledError(PackagingManagerException):
    """
    package is disabled error.
    """
    pass
