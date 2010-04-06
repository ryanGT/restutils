#!/usr/bin/env python

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.parsers import rst
from docutils import nodes
from docutils.core import publish_cmdline, default_description
from docutils.parsers.rst.roles import register_canonical_role
from docutils.writers.latex2e import Writer as Latex2eWriter
from docutils.writers.latex2e import LaTeXTranslator
from docutils.parsers.rst import directives
from var_to_latex import VariableToLatex
#!from pytexutils import lhs
import sys,traceback
#from pygments_code_block_directive import *
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import LatexFormatter
from docutils.parsers.rst.directives.images import Figure

def filterlhs(lhsin):
    """I had some problems with just grabbing everything to the left
    of the equals sign with Maxima output.  Sometimes there are very
    complicated expressions over there and I just want simple
    variables.  If lhsin is complicated, return an empty string."""
    badlist = ['\\left','\\right','\\frac','\\displaystyle','\\begin','\\end','\\,']
    for item in badlist:
        if item in lhsin:
            return ''
    if floatre.match(lhsin.strip()):#we aren't going to replace floating point or integer lhs's
        return ''
    return lhsin

    
def lhs(line):
    """Find the left hand side of a line with an equals sign."""
    lineout = line.strip()
    ind = lineout.find('=')
    if ind==-1:
        return ''
    myout = lineout[0:ind]
    myout = myout.strip()
    myout = filterlhs(myout)
    return myout


def parse_py_line(line):
    if line.find('=') != -1:
        l,r = line.split('=')
        return l,r
    else:
        return '',line


def py2latex(content,fmt='%0.4f'):
    for n,line in enumerate(content):
        curlhs,currhs = parse_py_line(line)
        try:
            exec line in sys.modules['__main__'].py_directive_namespace
        except:
            for i,l in enumerate(content):
                print '%s: %s'%(i+1,l)
            traceback.print_exc(file=sys.stdout)
            sys.exit(0)
        curvar = eval(currhs,sys.modules['__main__'].py_directive_namespace)
        try:
            curlatex = VariableToLatex(curvar,curlhs,fmt=fmt)[0][0]
        except:
            for i,l in enumerate(content):
                print '%s: %s'%(i+1,l)
            traceback.print_exc(file=sys.stdout)
            sys.exit(0)
            
        if n == 0:
            latex=curlatex
        else:
            latex+='\\\\'
            latex+=curlatex
        if n==len(content)-1 and len(content)>1:
                latex+='\\\\'
    return latex


# Executed py directives

# Define py node:
class py(nodes.Element):
    tagname = '#py'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

# Define pyno node:
class pyno(nodes.Element):
    tagname = '#pyno'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

class py_echo_area(nodes.Element):
    tagname= '#py_echo_area'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex


# Register role:
def py_role(role, rawtext, text, lineno, inliner,
                    options={}, content=[]):
    if not hasattr(sys.modules['__main__'],'py_directive_namespace'):
        setattr(sys.modules['__main__'],'py_directive_namespace', {})
    i = rawtext.find('`')
    code = rawtext[i+1:-1]+'\n'
    if options.has_key('fmt'):
        fmt = options['fmt']
    else:
        fmt = '%0.3f'
    try:
        latex = py2latex([code],fmt=fmt)
    except SyntaxError, msg:
        msg = inliner.reporter.error(msg, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    node = py(rawtext, latex)
    return [node], []

class code_block(nodes.Element):
    tagname = '#code_block'
    def __init__(self, rawsource, latex,language,formatter):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex
        self.language = language
        self.formatter = formatter
        
def code_block_role(role,rawtext,text,lineno,inliner,options={},content=[]):
    latex = text#'\\lstinline{%s}'%text
    if options.has_key('language'):
        language = options['language']
    else:
        language = 'python'
    formatter = 'listings'
    node = code_block(rawtext,latex,language,formatter)
    return [node],[]
    

class code_block_directive(rst.Directive):
    has_content = True

    required_arguments = 1
    options_spec = {
        'numbering':directives.unchanged,
        'formater':directives.unchanged,
        }


    def run(self):
        formatter = self.state.document.settings.code_block_formatter
        if self.options.has_key('formatter'):
            echo = self.options['formatter']
        else:
            formatter = 'listings'
        language = self.arguments[0]
        code = ''
        for line in self.content:
            code+='%s\n'%line
        if formatter == 'pygments':
            lexer = get_lexer_by_name(language)
            latex_tokens = pygments.lex(code, lexer)
            formatter = LatexFormatter()
            latex = pygments.format(latex_tokens,formatter)
        elif formatter == 'listings':
            latex = code
        node = code_block(self.block_text,latex,language,formatter)
        return [node]

        

class py_directive(rst.Directive):
    has_content = True
    # echo_values = ('verbatim','none')
    # format_values = ('%0.3f','%0.9f')
    
    # def format(argument):
    #     return directives.choice(argument, py_directive.format_values)

    # def echo(argument):
    #     return directives.choice(argument, py_directive.echo_values)

    option_spec = {'echo': directives.unchanged,
                   'fmt': directives.unchanged,
                   }
    


    def run(self):
        echo = self.state.document.settings.py_echo
        fmt = self.state.document.settings.py_fmt
        if not hasattr(sys.modules['__main__'],'py_directive_namespace'):
            setattr(sys.modules['__main__'],'py_directive_namespace', {})
        if self.options.has_key('echo'):
            echo = self.options['echo']
        if self.options.has_key('fmt'):
            fmt = self.options['fmt']
        echo_code_latex = ''
        if echo == 'verbatim':
            echo_code_latex = ""
            for n,l in enumerate(self.content):
                echo_code_latex += l
                if n != len(self.content)-1:
                    echo_code_latex += '\n'
        elif echo == 'none':
            echo_code_latex = ''
        latex = py2latex(self.content,fmt=fmt)
        py_node = py(self.block_text,latex)                
        if echo != 'none':
            echo_code = py_echo_area(self.block_text,echo_code_latex)
            return [echo_code,py_node]
        else:
            return [py_node]

class pyno_directive(rst.Directive):
    has_content = True


    option_spec = {'echo': directives.unchanged,
                   'fmt': directives.unchanged,
                   }

    def run(self):
        if not hasattr(sys.modules['__main__'],'py_directive_namespace'):
            setattr(sys.modules['__main__'],'py_directive_namespace', {})
        echo = self.state.document.settings.py_echo
        fmt = self.state.document.settings.py_fmt
        if not hasattr(sys.modules['__main__'],'py_directive_namespace'):
            setattr(sys.modules['__main__'],'py_directive_namespace', {})
        if self.options.has_key('echo'):
            echo = self.options['echo']
        if self.options.has_key('fmt'):
            fmt = self.options['fmt']
        echo_code_latex = ''
        if echo == 'verbatim':
            echo_code_latex = ""
            for n,l in enumerate(self.content):
                echo_code_latex += l
                if n != len(self.content)-1:
                    echo_code_latex += '\n'
        elif echo == 'none':
            echo_code_latex = ''
        latex = ''
        echo_code = py_echo_area(self.block_text,echo_code_latex)
        code = ''
        for n,line in enumerate(self.content):
            code+='%s\n'%line
        try:
            exec code in sys.modules['__main__'].py_directive_namespace
        except:
            for i,l in enumerate(code.split('\n')):
                print '%s: %s'%(i+1,l)
            traceback.print_exc(file=sys.stdout)
            sys.exit(0)
            
        py_node = pyno(self.block_text,latex)
        return [echo_code,py_node]


class jqfigure(nodes.General, nodes.Element):pass

class jqfigure_directive(Figure):

    option_spec = Figure.option_spec.copy()
    option_spec['placement'] = directives.unchanged

    def run(self):
        placement = self.state.document.settings.jqfigure_placement
        if self.options.has_key('placement'):
            placement = self.options['placement']
        (figure_node,) = Figure.run(self)
        jqfigure_node = jqfigure('',figure_node)
        jqfigure_node['placement'] = placement
        return [jqfigure_node]

def visit_py(self,node):
    inline = isinstance(node.parent, nodes.TextElement)
    attrs = node.attributes
    if inline:
        self.body.append('$%s$' % node.latex)
    else:
        self.body.extend(['\\begin{equation}\\begin{split}\n',
                          node.latex,
                          '\n\\end{split}\\end{equation}\n'])
def depart_py(self,node):
    pass

def visit_py_echo_area(self,node):
    self.body.extend(['\n\n\\begin{lstlisting}[language={python}]\n',node.latex,'\n\\end{lstlisting}\n'])

def depart_py_echo_area(self,node):
    pass

def visit_pyno(self,node):
    pass

def depart_pyno(self,node):
    pass

def visit_code_block(self,node):
    inline = isinstance(node.parent, nodes.TextElement)
    attrs = node.attributes
    if inline:
        self.body.append('\\lstinline{%s}' % node.latex)
    else:
        if node.formatter == 'pygments':
            lexer = get_lexer_by_name(language)
            latex_tokens = pygments.lex(code, lexer)
            formatter = LatexFormatter()
            latex = [pygments.format(latex_tokens,formatter)]
        elif node.formatter == 'listings':
            latex = ['\\begin{lstlisting}[language=%s]\n'%node.language,
                          node.latex,
                          '\n\\end{lstlisting}\n']
        self.body.extend(latex)

def depart_code_block(self,node):
    pass


def visit_jqfigure(self,node):
    pass

def depart_jqfigure(self,node):
    attrs = node.attributes
    placement_str = attrs['placement']
    if placement_str == '':
        placement = placement_str
    else:
        placement = '[%s]'%placement_str
    for i in range(len(self.out)):
        j = i+1
        cur = self.out[-j]
        if cur.find('begin') > -1 and cur.find('figure') > 1:
            self.out[-j] = cur+placement
            break

# Latex Math Stuff

# Define LaTeX math node:
class latex_math(nodes.Element):
    tagname = '#latex-math'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

# Register role:
def latex_math_role(role, rawtext, text, lineno, inliner,
                    options={'label':None}, content=[]):
    i = rawtext.find('`')
    latex = rawtext[i+1:-1]
    node = latex_math(rawtext, latex)
    return [node], []

class latex_math_directive(rst.Directive):
    has_content = True
    def run(self): 
        latex = ''.join(self.content)
        node = latex_math(self.block_text, latex)
        return [node]
# Add visit/depart methods to HTML-Translator:
def visit_latex_math(self, node):
    inline = isinstance(node.parent, nodes.TextElement)
    if inline:
        self.body.append('$%s$' % node.latex)
    else:
        self.body.extend(['\\begin{equation}\\begin{split}',
                          node.latex,
                          '\\end{split}\\end{equation}'])
        
def depart_latex_math(self, node):
    pass
    

# Register everything and add to Translator
py_role.options = {'class': None,'fmt': directives.unchanged}
py_role.options = {'class': None,'language': directives.unchanged}

register_canonical_role('latex-math', latex_math_role)
register_canonical_role('py', py_role)
register_canonical_role('code-block', code_block_role)

directives.register_directive('latex-math', latex_math_directive)
directives.register_directive('py', py_directive)
directives.register_directive('pyno', pyno_directive)
directives.register_directive('code-block', code_block_directive)
directives.register_directive('jqfigure', jqfigure_directive)


LaTeXTranslator.visit_latex_math = visit_latex_math
LaTeXTranslator.depart_latex_math = depart_latex_math
LaTeXTranslator.visit_py = visit_py
LaTeXTranslator.depart_py = depart_py
LaTeXTranslator.visit_pyno = visit_pyno
LaTeXTranslator.depart_pyno = depart_pyno
LaTeXTranslator.visit_py_echo_area = visit_py_echo_area
LaTeXTranslator.depart_py_echo_area = depart_py_echo_area
LaTeXTranslator.visit_code_block = visit_code_block
LaTeXTranslator.depart_code_block = depart_code_block
LaTeXTranslator.visit_jqfigure = visit_jqfigure
LaTeXTranslator.depart_jqfigure = depart_jqfigure


# Publish the commandline
Latex2eWriter.settings_spec = (Latex2eWriter.settings_spec[0],\
                               Latex2eWriter.settings_spec[1],\
                               Latex2eWriter.settings_spec[2] + \
                               (('Specify default echo. Default is "none".',\
                                 ['--py-echo'],\
                                 {'default':'none'}),\
                                ('Specify format of floats. Default is "%0.4f".',\
                                 ['--py-fmt'],\
                                 {'default':'%0.4f'}),
                                ('Specify formatter for code blocks. Default is python.',\
                                 ['--code-block-formatter'],\
                                 {'default':'python'}),
                                ('Specify formatter for code blocks. Default is [tbp!].',\
                                 ['--jqfigure-placement'],\
                                 {'default':'tbp!'})
                                ))

description = ('Generates LaTeX documents from standalone reStructuredText '
               'sources.  ' + default_description)

publish_cmdline(writer_name='latex', description=description)







    
