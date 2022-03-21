import os
import pathlib

import versioneer

__author__ = "Ali-Akber Saifee"
__email__ = "ali@indydevs.org"
__copyright__ = "Copyright 2022, Ali-Akber Saifee"

from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension

THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def get_requirements(req_file):
    requirements = []

    for r in open(os.path.join(THIS_DIR, "requirements", req_file)).read().splitlines():
        if r.strip():
            requirements.append(r.strip())

    return requirements


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
    project_urls={
        "Source": "https://github.com/alisaifee/coredis",
        "Documentation": "https://coredis.readthedocs.org",
    },
    author=__author__,
    author_email=__email__,
    maintainer=__author__,
    maintainer_email=__email__,
    keywords=["Redis", "key-value store", "asyncio"],
    license="MIT",
    packages=find_packages(exclude=["tests", "benchmarks"]),
    package_data={
        "coredis": ["py.typed"],
    },
    python_requires=">=3.8",
    install_requires=get_requirements("main.txt"),
    extras_require={"hiredis": ["hiredis>=2.0.0"]},
    cmdclass=versioneer.get_cmdclass({"build_ext": custom_build_ext}),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    ext_modules=[
        Extension(name="coredis.speedups", sources=["coredis/speedups.c"]),
    ],
)
