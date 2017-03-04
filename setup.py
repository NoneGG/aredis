#!/usr/bin/env python
import os
import sys
from aredis import __version__


try:
    from setuptools import setup
    from setuptools.command.test import test as TestCommand

    class PyTest(TestCommand):
        def finalize_options(self):
            TestCommand.finalize_options(self)
            self.test_args = []
            self.test_suite = True

        def run_tests(self):
            # import here, because outside the eggs aren't loaded
            import pytest
            errno = pytest.main(self.test_args)
            sys.exit(errno)

except ImportError:

    from distutils.core import setup

    def PyTest(x):
        x

f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
long_description = f.read()
f.close()

setup(
    name='aredis',
    version=__version__,
    description='Python async client for Redis key-value store',
    long_description=long_description,
    url='https://github.com/NoneGG/aredis',
    author='Jason Chen',
    author_email='847671011@qq.com',
    maintainer='Jason Chen',
    maintainer_email='847671011@qq.com',
    keywords=['Redis', 'key-value store', 'asyncio'],
    license='MIT',
    packages=['aredis', 'aredis.commands'],
    tests_require=['pytest',
                   'pytest_asyncio>=0.5.0'],
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ]
)
