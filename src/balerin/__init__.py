# -*- coding: utf-8 -*-
"""
balerin package.

balerin is a python package startup orchestrator. it can handle loading all
packages of an application at startup time respecting package dependencies.
"""

from balerin.packaging.base import Package
from balerin.packaging.manager import PackagingManager


__version__ = '0.1.4'
