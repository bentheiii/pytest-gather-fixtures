# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------
from enum import EnumMeta
from importlib import import_module
from importlib.util import find_spec
from inspect import getsourcefile, getsourcelines
from pathlib import Path
import subprocess
from traceback import print_exc
from unittest.mock import Mock

project = 'pytest-gather-fixtures'
copyright = '2021, Ben Avrahami'
author = 'Ben Avrahami'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.intersphinx", 'sphinx.ext.linkcode', 'sphinx.ext.autosectionlabel', 'sphinx_copybutton'
]

autosectionlabel_prefix_document = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

python_use_unqualified_type_names = True

import ast
import os
from sluth import NodeWalk

release = 'main'
if rtd_version := os.environ.get("READTHEDOCS_GIT_IDENTIFIER"):
    release = rtd_version
else:
    # try to get the current branch name
    try:
        release = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
    except Exception:
        pass

source_root = "pytest_gather_fixtures"
root_dir = Path(find_spec(source_root).submodule_search_locations[0])
base_url = "https://github.com/bentheiii/pytest-gather-fixtures"


def linkcode_resolve(domain, info):
    if domain != "py":
        return None
    try:
        package_file = root_dir / (info["module"].replace(".", "/") + ".py")
        if not package_file.exists():
            package_file = root_dir / info["module"].replace(".", "/") / "__init__.py"
            if not package_file.exists():
                raise FileNotFoundError
        blob = source_root / Path(package_file).relative_to(root_dir)
        walk = NodeWalk.from_file(package_file)
        try:
            decl = walk.get_last(info["fullname"])
        except KeyError:
            return None
    except Exception as e:
        print(f"error getting link code {info}")
        print_exc()
        raise
    return f"{base_url}/blob/{release}/{blob}#L{decl.lineno}-L{decl.end_lineno}"


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []
