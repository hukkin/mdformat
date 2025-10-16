# fmt: off
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

project = 'mdformat'
copyright = '2021, Taneli Hukkinen'  # noqa: A001
author = 'Taneli Hukkinen'

# The full version, including alpha/beta/rc tags
release = '1.0.0'  # DO NOT EDIT THIS LINE MANUALLY. LET bump2version UTILITY DO IT


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['myst_parser']

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
html_logo = "_static/logo-150px.png"
html_show_sphinx = False

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Options for MyST parser -------------------------------------------------

# Disable MyST syntax incompatible with vanilla mdformat
# (i.e. disable everything except "directives")
myst_disable_syntax = [
    "table",
    "front_matter",
    "myst_line_comment",
    "myst_block_break",
    "myst_target",
    "myst_role",
    "math_inline",
    "math_block",
    "footnote_def",
    "footnote_inline",
    "footnote_ref",
    "footnote_tail",
]
