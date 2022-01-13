#!/usr/bin/env python
import pathlib
import re
import sys
import versioneer

__author__ = "Ali-Akber Saifee"
__email__ = "ali@indydevs.org"
__copyright__ = "Copyright 2022, Ali-Akber Saifee"

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
    NOTE: This code was originally taken from tornado.

    Allows C extension building to fail.

    The C extension speeds up crc16, but is not essential.
    """

    warning_message = """
********************************************************************
{target} could not
be compiled. No C extensions are essential for coredis to run,
although they do result in significant speed improvements for
websockets.
{comment}

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

https://api.mongodb.org/python/current/installation.html#osx
********************************************************************
"""

    def run(self):
        try:
            super().run()
        except Exception as e:
            self.warn(e)
            self.warn(
                self.warning_message.format(
                    target="Extension modules",
                    comment=(
                        "There is an issue with your platform configuration "
                        "- see above."
                    ),
                )
            )

    def build_extension(self, ext):
        try:
            super().build_extension(ext)
        except Exception as e:
            self.warn(e)
            self.warn(
                self.warning_message.format(
                    target="The {} extension ".format(ext.name),
                    comment=(
                        "The output above this warning shows how the "
                        "compilation failed."
                    ),
                )
            )


_ROOT_DIR = pathlib.Path(__file__).parent

with open(str(_ROOT_DIR / "README.rst")) as f:
    long_description = f.read()

setup(
    name="coredis",
    version=versioneer.get_version(),
    description="Python async client for Redis key-value store",
    long_description=long_description,
    url="https://github.com/alisaifee/coredis",
    author=__author__,
    author_email=__email__,
    maintainer=__author__,
    maintainer_email=__email__,
    keywords=["Redis", "key-value store", "asyncio"],
    license="MIT",
    packages=["coredis", "coredis.commands"],
    python_requires=">=3.7",
    extras_require={"hiredis": ["hiredis>=0.2.0"]},
    tests_require=["pytest", "pytest_asyncio>=0.5.0"],
    cmdclass=versioneer.get_cmdclass({"test": PyTest, "build_ext": custom_build_ext}),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    ext_modules=[Extension(name="coredis.speedups", sources=["coredis/speedups.c"]),],
)
