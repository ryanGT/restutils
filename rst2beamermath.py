#!/usr/bin/env python
# encoding: utf-8

'''
See rst2beamer.py and rst2latexmath.py for more information.
'''

from rst2beamer import BeamerTranslator, BeamerWriter,default_description,publish_cmdline
from rst2latexmath import visit_latex_math,depart_latex_math

BeamerTranslator.visit_latex_math = visit_latex_math
BeamerTranslator.depart_latex_math = depart_latex_math


if __name__ == '__main__':
        description = (
                "Generates Beamer-flavoured LaTeX for PDF-based presentations with LaTeX math support." + default_description)
        publish_cmdline (writer=BeamerWriter(), description=description)

