# -*- coding: utf-8 -*-

import os
import io
from setuptools import setup, find_packages


# Helpers
def read(*paths):
    """Read a text file."""
    basedir = os.path.dirname(__file__)
    fullpath = os.path.join(basedir, *paths)
    contents = io.open(fullpath, encoding='utf-8').read().strip()
    return contents


# Prepare
PACKAGE = 'metastore'
NAME = 'metastore'
INSTALL_REQUIRES = [
    'flask',
    'flask-cors',
    'flask-jsonpify',
    'pyyaml',
    'requests',
    'pyjwt',
    'cryptography',
    'elasticsearch>=5.0.0,<6.0.0'
]
TESTS_REQUIRE = [
    'pytest',
    'pytest-cov',
    'pylama',
    'coverage',
    'coveralls',
    'tox'
]
README = read('README.md')
VERSION = read(PACKAGE, 'VERSION')
PACKAGES = find_packages(exclude=['examples', 'tests'])


# Run
setup(
    name=NAME,
    version=VERSION,
    packages=PACKAGES,
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    extras_require={'develop': TESTS_REQUIRE},
    zip_safe=False,
    long_description=README,
    description='{{ DESCRIPTION }}',
    author='Open Knowledge (International), Datopian and DataHQ',
    url='https://github.com/datahq/bitstore',
    license='MIT',
    keywords=[
        'data',
        'analytics'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
