#!/usr/bin/env python
import os
import sys
import warnings

from aredis import __version__

try:
    from setuptools import setup
    from setuptools.command.test import test as TestCommand
    from setuptools.command.build_ext import build_ext
    from setuptools.extension import Extension


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

    from distutils.core import setup, Extension
    from distutils.command.build_ext import build_ext


    def PyTest(x):
        x


class custom_build_ext(build_ext):
    """
    These code comes from tornado.
    Allow C extension building to fail.

    The C extension speeds up crc16, but is not essential.
    """

    warning_message = """
********************************************************************
WARNING: %s could not
be compiled. No C extensions are essential for aredis to run,
although they do result in significant speed improvements for
websockets.
%s

Here are some hints for popular operating systems:

If you are seeing this message on Linux you probably need to
install GCC and/or the Python development package for your
version of Python.

Debian and Ubuntu users should issue the following command:

    $ sudo apt-get install build-essential python-dev

RedHat and CentOS users should issue the following command:

    $ sudo yum install gcc python-devel

Fedora users should issue the following command:

    $ sudo dnf install gcc python-devel

If you are seeing this message on OSX please read the documentation
here:

http://api.mongodb.org/python/current/installation.html#osx
********************************************************************
"""

    def run(self):
        try:
            build_ext.run(self)
        except Exception:
            e = sys.exc_info()[1]
            sys.stdout.write('%s\n' % str(e))
            warnings.warn(self.warning_message % ("Extension modules",
                                                  "There was an issue with "
                                                  "your platform configuration"
                                                  " - see above."))

    def build_extension(self, ext):
        name = ext.name
        try:
            build_ext.build_extension(self, ext)
        except Exception:
            e = sys.exc_info()[1]
            sys.stdout.write('%s\n' % str(e))
            warnings.warn(self.warning_message % ("The %s extension "
                                                  "module" % (name,),
                                                  "The output above "
                                                  "this warning shows how "
                                                  "the compilation "
                                                  "failed."))


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
    cmdclass={
        'test': PyTest,
        'build_ext': custom_build_ext
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    ext_modules=[
        Extension(name='aredis.speedups',
                  sources=['aredis/speedups.c']),
    ]
)
