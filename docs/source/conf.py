#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath("../../"))
sys.path.insert(0, os.path.abspath("./"))

import coredis
import coredis.sentinel

from theme_config import *

master_doc = "index"
project = "coredis"
copyright = "2107, NoneGG | 2022, Ali-Akber Saifee"
author = "alisaifee"
description = "Async redis client for python"

html_static_path = ["./_static"]
html_css_files = [
    "custom.css",
    "https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;700&family=Fira+Sans:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap",
]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinxext.opengraph",
    "sphinx_copybutton",
    "sphinx.ext.viewcode",
    "sphinx_paramlinks",
]

autodoc_default_options = {
    "members": True,
    "inherited-members": True,
    "inherit-docstrings": True,
    "member-order": "bysource",
}


version, _ = release, part = coredis.__version__.split("+")

html_title = f"{project} <small><b style='color: var(--color-brand-primary)'>{{{release}}}</b></small>"
try:
    ahead = int(part.rsplit(".")[0])
    if ahead > 0:
        html_theme_options["announcement"] = f"""
        This is a development version. The documentation for the latest version: <b>{release}</b> can be found <a href="/en/stable">here</a>
        """
        html_title = f"{project} <small><b style='color: var(--color-brand-primary)'>{{dev}}</b></small>"
except:
    pass

add_module_names = False
autoclass_content = "both"
autodoc_typehints_format = "short"

autosectionlabel_maxdepth = 2
autosectionlabel_prefix_document = True

extlinks = {"pypi": ("https://pypi.org/project/%s", "%s")}

htmlhelp_basename = "coredisdoc"
latex_elements = {}

latex_documents = [
    (master_doc, "coredis.tex", "coredis Documentation", "alisaifee", "manual"),
]
man_pages = [(master_doc, "coredis", "coredis Documentation", [author], 1)]

texinfo_documents = [
    (
        master_doc,
        "coredis",
        "coredis Documentation",
        author,
        "coredis",
        "One line description of project.",
        "Miscellaneous",
    ),
]
intersphinx_mapping = {
    "https://docs.python.org/": None,
    "redis-py": ("https://redis-py.readthedocs.io/en/latest/", None),
}
