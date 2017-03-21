#!/usr/bin/env python
# vim: set sw=4 et:

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import glob

from har2warc import __version__

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)

    def run_tests(self):
        import pytest
        import sys
        import os
        errcode = pytest.main(['--doctest-module', './har2warc', '--cov', 'har2warc', '-v', 'test/'])
        sys.exit(errcode)


setup(
    name='har2warc',
    version=__version__,
    author='Ilya Kreymer',
    author_email='ikreymer@gmail.com',
    license='Apache 2.0',
    packages=find_packages(),
    url='https://github.com/webrecorder/har2warc',
    description='Convert HTTP Archive (HAR) -> Web Archive (WARC) format',
    long_description=open('README.rst').read(),
    provides=[
        'har2warc'
        ],
    install_requires=[
        'warcio',
        'six',
        'http_status',
        ],
    zip_safe=True,
    data_files=[
        ('test/data', glob.glob('test/data/*')),
    ],
    entry_points="""
        [console_scripts]
        har2warc = har2warc.har2warc:main
    """,
    cmdclass={'test': PyTest},
    test_suite='',
    tests_require=[
        'pytest',
        'pytest-cov',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ]
)
