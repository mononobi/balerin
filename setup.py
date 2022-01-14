# -*- coding: utf-8 -*-
"""
balerin setup module.
"""

import io
import re

from setuptools import find_namespace_packages, setup


with io.open('README.md', 'rt', encoding='utf8') as readme_file:
    README = readme_file.read()

with io.open('src/balerin/__init__.py', 'rt', encoding='utf8') as version_file:
    VERSION = re.search(r"__version__ = '(.*?)'", version_file.read()).group(1)

PACKAGES = []

setup(
    name='balerin',
    version=VERSION,
    url='https://github.com/mononobi/balerin',
    project_urls={
        # 'Documentation': '',
        'Code': 'https://github.com/mononobi/balerin',
        'Issue tracker': 'https://github.com/mononobi/balerin/issues',
    },
    license='BSD-3-Clause',
    author='Mohamad Nobakht',
    author_email='mohamadnobakht@gmail.com',
    maintainer='Mohamad Nobakht',
    maintainer_email='mohamadnobakht@gmail.com',
    description='A python package startup orchestrator. it can handle loading all packages '
                'of an application at startup time respecting package dependencies.',

    long_description=README,
    long_description_content_type='text/markdown',
    keywords=('python balerin package-manager packaging startup auto-import'
              'startup-import syntax-error package-loader'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_namespace_packages('src', exclude=('tests', 'tests.*')),
    package_dir={'': 'src'},
    package_data={'': ['*']},
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=PACKAGES
)
