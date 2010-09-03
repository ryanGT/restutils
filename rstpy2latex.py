#!/usr/bin/env python

"""
A minimal front end to the Docutils Publisher, producing LaTeX.
"""

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.parsers.rst.roles import register_canonical_role
from docutils import nodes
from docutils.core import publish_cmdline
#from docutils.writers.latex2e import LaTeXTranslator
from docutils.core import default_usage, default_description, Publisher
from restutils import Latex2eWriter,LaTeXTranslator


description = ('Generates LaTeX documents from standalone reStructuredText '
               'sources.  ' + default_description)

publish_cmdline(writer_name='latex', description=description)
