#
# restutils
# =========
# 
"""
Restutils is an extention to the standard docutils package.  
"""

import sys,traceback,pygments,pdb

from docutils import nodes
from docutils.writers.latex2e import Writer as Latex2eWriter
from docutils.writers.latex2e import LaTeXTranslator
from docutils.parsers.rst.roles import register_canonical_role
from docutils.parsers.rst import directives, Directive
from docutils.parsers.rst.directives.images import Figure
from docutils.writers.latex2e import PreambleCmds

from pygments.lexers import get_lexer_by_name
from pygments.formatters import LatexFormatter

from sympy import N
from sympy.printing.latex import LatexPrinter as SympyLatexPrinter

from var_to_latex import ArrayToLaTex

__version__="0.1"
__version_details__=""

class LatexPrinter(SympyLatexPrinter):
    def _print_ndarray(self, expr):
        out_str = ArrayToLaTex(expr,'')[0]
        if type(out_str) == list:
            out_str = '\n'.join(out_str)
        return out_str 


def load_replacement_list(replacement_file):
    f = open(replacement_file, 'rb')
    lines = f.readlines()
    f.close()
    find_list = []
    replace_list = []
    for line in lines:
        f, r = line.split('&',1)
        find_list.append(f.strip())
        replace_list.append(r.strip())
    return find_list, replace_list


def _replace_latex(latex, find_list, replace_list):
    latex_out = latex
    for find_str, replace_str in zip(find_list, replace_list):
        latex_out = latex_out.replace(find_str, replace_str)
    return latex_out


def replace_latex(latex, replacement_file):
    find_list, replace_list = load_replacement_list(replacement_file)
    latex_out = _replace_latex(latex, find_list, replace_list)
    return latex_out


def py2latex(content,prec=4,fmt="%0.4f",replacement_file=None):
    for n,line in enumerate(content):
        if line.find("="): curlhs, currhs = line.split("=")
        else: curlhs, currhs = '',line
        try:
            exec line in sys.modules['__main__'].py_directive_namespace
        except:
            for i,l in enumerate(content):
                print '%s: %s'%(i+1,l)
            traceback.print_exc(file=sys.stdout)
            sys.exit(0)
        curvar = eval(currhs,sys.modules['__main__'].py_directive_namespace)
        try:
            settings = {'mat_str':'bmatrix','mat_delim':None, \
                        'wrap':'none','inline':False}                        
            curlatex = LatexPrinter(settings).doprint(curvar)
        except:
            for i,l in enumerate(content):
                print '%s: %s'%(i+1,l)
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)
        if curlhs != '':
            curlatex = unicode(curlatex,"utf-8").replace('dimensionless','')
            curlatex = '%s = %s'%(curlhs,curlatex)
        if n == 0:
            latex=curlatex
        else:
            latex+='\\\\'
            latex+=curlatex
        if n==len(content)-1 and len(content)>1:
                latex+='\\\\'
    if replacement_file:
        latex = replace_latex(latex, replacement_file)#probably bad to load the file many times
    return latex

#========================================
# Nodes
#========================================

class latex_math(nodes.Element):
    tagname = '#latex-math'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

class py(nodes.Element):
    tagname = '#py'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

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

class code_block(nodes.Element):
    tagname = '#code_block'
    def __init__(self, rawsource, latex,language,formatter):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex
        self.language = language
        self.formatter = formatter

class jqfigure(nodes.General, nodes.Element):pass

#========================================
# Roles
#========================================

def latex_math_role(role, rawtext, text, lineno, inliner,
                    options={'label':None}, content=[]):
    i = rawtext.find('`')
    latex = rawtext[i+1:-1]
    node = latex_math(rawtext, latex)
    return [node], []

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

py_role.options = {'class': None,'fmt': directives.unchanged}
py_role.options = {'class': None,'language': directives.unchanged}
        
def code_block_role(role,rawtext,text,lineno,inliner,options={},content=[]):
    latex = text#'\\lstinline{%s}'%text
    if options.has_key('language'):
        language = options['language']
    else:
        language = 'python'
    formatter = 'listings'
    node = code_block(rawtext,latex,language,formatter)
    return [node],[]

#========================================
# Directives
#========================================

class latex_math_directive(Directive):
    has_content = True
    option_spec = {
        'numbered':directives.unchanged,
        }

    def run(self): 
        latex = ''.join(self.content)
        node = latex_math(self.block_text, latex)
        node.number_equation = self.state.document.settings.number_equations
        if self.options.has_key('numbered'):
            if self.options['numbered'] in ['true','True']:
                node.number_equation = True
            elif self.options['numbered'] in ['false','False']:
                node.number_equation = False
        return [node]

class py_directive(Directive):
    has_content = True
    option_spec = {'echo': directives.unchanged,
                   'fmt': directives.unchanged,
                   'label': directives.unchanged,
                   'numbered':directives.unchanged,
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
        if self.options.has_key('label'):
            label = self.options['label']
        else:
            label = None
        echo_code_latex = ''
        if echo == 'verbatim':
            echo_code_latex = ""
            for n,l in enumerate(self.content):
                echo_code_latex += l
                if n != len(self.content)-1:
                    echo_code_latex += '\n'
        elif echo == 'none':
            echo_code_latex = ''
        replace_path = ''
        if self.state.document.settings.replacement_file:
            replace_path = self.state.document.settings.replacement_file
        latex = py2latex(self.content,fmt=fmt,replacement_file=replace_path)
        py_node = py(self.block_text,latex)                
        if label:
            py_node.label = label
        py_node.number_equation = self.state.document.settings.number_equations
        if self.options.has_key('numbered'):
            if self.options['numbered'] in ['true','True']:
                py_node.number_equation = True
            elif self.options['numbered'] in ['false','False']:
                py_node.number_equation = False
        if echo != 'none':
            echo_code = py_echo_area(self.block_text,echo_code_latex)
            return [echo_code,py_node]
        else:
            return [py_node]

class pyno_directive(Directive):
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

class code_block_directive(Directive):
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
        
class jqfigure_directive(Figure):

    option_spec = Figure.option_spec.copy()
    option_spec['placement'] = directives.unchanged

    def run(self):
        pdb.set_trace()
        placement = self.state.document.settings.jqfigure_placement
        if self.options.has_key('placement'):
            placement = self.options['placement']
        (figure_node,) = Figure.run(self)
        jqfigure_node = jqfigure('',figure_node)
        jqfigure_node['placement'] = placement
        return [jqfigure_node]

#========================================
# Visit/Departs
#========================================

def visit_latex_math(self, node):
    self.requirements['math'] = r'\usepackage{amsmath}'
    inline = isinstance(node.parent, nodes.TextElement)
    if inline:
        self.body.append('$%s$' % node.latex)
    else:
        if node.number_equation:
            env = 'equation'
        else:
            env = 'equation*'
        self.body.extend(['\\begin{%s}\\begin{split}'%env,
                          node.latex,
                          '\\end{split}\\end{%s}'%env])
        
def depart_latex_math(self, node):
    pass
    
def visit_py(self,node):
    self.requirements['math'] = r'\usepackage{amsmath}'
    inline = isinstance(node.parent, nodes.TextElement)
    attrs = node.attributes
    if inline:
        self.body.append('$%s$' % node.latex)
    else:
        if node.number_equation:
            env = 'equation'
        else:
            env = 'equation*'
        if hasattr(node,'label') and node.label:
            self.body.extend(['\\begin{%s}\\begin{split}\n'%env,
                              '\\label{%s}'%node.label,
                              node.latex,
                              '\n\\end{split}\\end{%s}\n'%env])
        else:
            self.body.extend(['\\begin{%s}\\begin{split}\n'%env,
                              node.latex,
                              '\n\\end{split}\\end{%s}\n'%env])
            
def depart_py(self,node):
    pass

def visit_pyno(self,node):
    pass

def depart_pyno(self,node):
    pass

def visit_py_echo_area(self,node):
    self.requirements['listings'] = r'\usepackage{listings}'
    self.body.extend(['\n\n\\begin{lstlisting}[language={python}]\n',node.latex,'\n\\end{lstlisting}\n'])

def depart_py_echo_area(self,node):
    pass

def visit_code_block(self,node):
    inline = isinstance(node.parent, nodes.TextElement)
    attrs = node.attributes
    if inline:
        self.requirements['listings'] = r'\usepackage{listings}'
        self.body.append('\\lstinline{%s}' % node.latex)
    else:
        if node.formatter == 'pygments':
            lexer = get_lexer_by_name(language)
            latex_tokens = pygments.lex(code, lexer)
            formatter = LatexFormatter()
            latex = [pygments.format(latex_tokens,formatter)]
        elif node.formatter == 'listings':
            self.requirements['listings'] = r'\usepackage{listings}'
            latex = ['\\begin{lstlisting}[language=%s]\n'%node.language,
                          node.latex,
                          '\n\\end{lstlisting}\n']
        self.body.extend(latex)

def depart_code_block(self,node):
    pass

def visit_jqfigure(self,node):
    pass

## def visit_figure(self, node):
##     pdb.set_trace()
##     self.requirements['float_settings'] = PreambleCmds.float_settings
##     # ! the 'align' attribute should set "outer alignment" !
##     # For "inner alignment" use LaTeX default alignment (similar to HTML)
##     ## if ('align' not in node.attributes or
##     ##     node.attributes['align'] == 'center'):
##     ##     align = '\n\\centering'
##     ##     align_end = ''
##     ## else:
##     ##     # TODO non vertical space for other alignments.
##     ##     align = '\\begin{flush%s}' % node.attributes['align']
##     ##     align_end = '\\end{flush%s}' % node.attributes['align']
##     ## self.out.append( '\\begin{figure}%s\n' % align )
##     ## self.context.append( '%s\\end{figure}\n' % align_end )
##     self.out.append('\\begin{figure}')
##     if node.get('ids'):
##         self.out += ['\n'] + self.ids_to_labels(node)
    
def visit_image(self, node):
    self.requirements['graphicx'] = self.graphicx_package
    attrs = node.attributes
    # Add image URI to dependency list, assuming that it's
    # referring to a local file.
    self.settings.record_dependencies.add(attrs['uri'])
    # alignment defaults:
    if not 'align' in attrs:
        # Set default align of image in a figure to 'center'
        if isinstance(node.parent, nodes.figure):
            attrs['align'] = 'center'
        # query 'align-*' class argument
        for cls in node['classes']:
            if cls.startswith('align-'):
                attrs['align'] = cls.split('-')[1]
    # pre- and postfix (prefix inserted in reverse order)
    pre = []
    post = []
    include_graphics_options = []
    display_style = ('block-', 'inline-')[self.is_inline(node)]
    align_codes = {
        # inline images: by default latex aligns the bottom.
        'bottom': ('', ''),
        'middle': (r'\raisebox{-0.5\height}{', '}'),
        'top':    (r'\raisebox{-\height}{', '}'),
        # block level images:
        'center': (r'\noindent\makebox[\textwidth][c]{', '}'),
        #'center': ('',''),
        'left':   (r'\noindent{', r'\hfill}'),
        'right':  (r'\noindent{\hfill', '}'),}
    if 'align' in attrs:
        try:
            align_code = align_codes[attrs['align']]
            pre.append(align_code[0])
            post.append(align_code[1])
        except KeyError:
            pass                    # TODO: warn?
    if 'height' in attrs:
        include_graphics_options.append('height=%s' %
                        self.to_latex_length(attrs['height']))
    if 'scale' in attrs:
        include_graphics_options.append('scale=%f' %
                                        (attrs['scale'] / 100.0))
    if 'width' in attrs:
        include_graphics_options.append('width=%s' %
                        self.to_latex_length(attrs['width']))
    if not self.is_inline(node):
        pre.append('\n')
        post.append('\n')
    pre.reverse()
    self.out.extend(pre)
    options = ''
    if include_graphics_options:
        options = '[%s]' % (','.join(include_graphics_options))
    self.out.append('\\includegraphics%s{%s}' % (options, attrs['uri']))
    self.out.extend(post)


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

#========================================
# Register roles and directives
#========================================

register_canonical_role('latex-math', latex_math_role)
register_canonical_role('py', py_role)
register_canonical_role('code-block', code_block_role)

directives.register_directive('latex-math', latex_math_directive)
directives.register_directive('py', py_directive)
directives.register_directive('pyno', pyno_directive)
directives.register_directive('code-block', code_block_directive)
directives.register_directive('jqfigure', jqfigure_directive)

#========================================
# Add methods to LaTeXTranslator
#========================================

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
#LaTeXTranslator.visit_figure = visit_figure
LaTeXTranslator.visit_image = visit_image

#========================================
# Modify commandline 
#========================================

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
                                 {'default':'tbp!'}),
                                ('Turn on equation numbering.',\
                                 ['--number-equations'],\
                                 {'action': 'store_true','default':False}),
                                ('Specify filepath for search and replace of LaTeX output.',\
                                 ['--replacement-file'],\
                                 {'default':''}),
                                ))
