"""
Exports the following:

:Classes:
    - `StandardTestCase`
    - `CustomTestCase`
    - `WriterPublishTestCase`
"""
__docformat__ = 'reStructuredText'

import sys
import os
import unittest
import re
import inspect
import traceback
from pprint import pformat

testroot = os.path.abspath(os.path.dirname(__file__) or os.curdir)
os.chdir(testroot)
sys.path.insert(0, os.path.normpath(os.path.join(testroot, '..')))
sys.path.insert(0, testroot)
sys.path.append(os.path.normpath(os.path.join(testroot, '..', 'extras')))

try:
    import difflib
    import package_unittest
    import restutils, docutils
    from docutils.parsers.rst import roles
    from docutils.readers import standalone
    from docutils.statemachine import StringList
    from docutils._compat import bytes
except ImportError:
    # The importing module (usually __init__.py in one of the
    # subdirectories) may catch ImportErrors in order to detect the
    # absence of DocutilsTestSupport in sys.path.  Thus, ImportErrors
    # resulting from problems with importing Docutils modules must
    # caught here.
    traceback.print_exc()
    sys.exit(1)


try:
    import mypdb as pdb
except:
    import pdb


# Hack to make repr(StringList) look like repr(list):
StringList.__repr__ = StringList.__str__


class DevNull:

    """Output sink."""

    def write(self, string):
        pass

    def close(self):
        pass


class StandardTestCase(unittest.TestCase):

    """
    Helper class, providing the same interface as unittest.TestCase,
    but with useful setUp and comparison methods.
    """

    def setUp(self):
        os.chdir(testroot)

    def failUnlessEqual(self, first, second, msg=None):
        """Fail if the two objects are unequal as determined by the '=='
           operator.
        """
        if not first == second:
            raise self.failureException, \
                  (msg or '%s != %s' % _format_str(first, second))

    def failIfEqual(self, first, second, msg=None):
        """Fail if the two objects are equal as determined by the '=='
           operator.
        """
        if first == second:
            raise self.failureException, \
                  (msg or '%s == %s' % _format_str(first, second))

    # Synonyms for assertion methods

    assertEqual = assertEquals = failUnlessEqual

    assertNotEqual = assertNotEquals = failIfEqual


class CustomTestCase(StandardTestCase):
    
    """
    Helper class, providing extended functionality over unittest.TestCase.

    The methods failUnlessEqual and failIfEqual have been overwritten
    to provide better support for multi-line strings.  Furthermore,
    see the compare_output method and the parameter list of __init__.
    """

    compare = difflib.Differ().compare
    """Comparison method shared by all subclasses."""

    def __init__(self, method_name, input, expected, id, run_in_debugger=0,
                 suite_settings=None):
        """
        Initialise the CustomTestCase.

        Arguments:

        method_name -- name of test method to run.
        input -- input to the parser.
        expected -- expected output from the parser.
        id -- unique test identifier, used by the test framework.
        run_in_debugger -- if true, run this test under the pdb debugger.
        suite_settings -- settings overrides for this test suite.
        """
        self.id = id
        self.input = input
        self.expected = expected
        self.run_in_debugger = run_in_debugger
        self.suite_settings = suite_settings.copy() or {}
        
        # Ring your mother.
        unittest.TestCase.__init__(self, method_name)

    def __str__(self):
        """
        Return string conversion. Overridden to give test id, in addition to
        method name.
        """
        return '%s; %s' % (self.id, unittest.TestCase.__str__(self))

    def __repr__(self):
        return "<%s %s>" % (self.id, unittest.TestCase.__repr__(self))

    def clear_roles(self):
        # Language-specific roles and roles added by the
        # "default-role" and "role" directives are currently stored
        # globally in the roles._roles dictionary.  This workaround
        # empties that dictionary.
        roles._roles = {}

    def setUp(self):
        StandardTestCase.setUp(self)
        self.clear_roles()

    def compare_output(self, input, output, expected):
        """`input`, `output`, and `expected` should all be strings."""
        if isinstance(input, unicode):
            input = input.encode('raw_unicode_escape')
        if sys.version_info > (3,):
            # API difference: Python 3's node.__str__ doesn't escape
            #assert expected is None or isinstance(expected, unicode)
            if isinstance(expected, bytes):
                expected = expected.decode('utf-8')
            if isinstance(output, bytes):
                output = output.decode('utf-8')
        else:
            if isinstance(expected, unicode):
                expected = expected.encode('raw_unicode_escape')
            if isinstance(output, unicode):
                output = output.encode('raw_unicode_escape')
        # Normalize line endings:
        if expected:
            expected = '\n'.join(expected.splitlines())
        if output:
            output = '\n'.join(output.splitlines())
        try:
            self.assertEquals(output, expected)
        except AssertionError, error:
            print >>sys.stderr, '\n%s\ninput:' % (self,)
            print >>sys.stderr, input
            try:
                comparison = ''.join(self.compare(expected.splitlines(1),
                                                  output.splitlines(1)))
                print >>sys.stderr, '-: expected\n+: output'
                print >>sys.stderr, comparison
            except AttributeError:      # expected or output not a string
                # alternative output for non-strings:
                print >>sys.stderr, 'expected: %r' % expected
                print >>sys.stderr, 'output:   %r' % output
            raise error

class CustomTestSuite(unittest.TestSuite):

    """
    A collection of CustomTestCases.

    Provides test suite ID generation and a method for adding test cases.
    """

    id = ''
    """Identifier for the TestSuite. Prepended to the
    TestCase identifiers to make identification easier."""

    next_test_case_id = 0
    """The next identifier to use for non-identified test cases."""

    def __init__(self, tests=(), id=None, suite_settings=None):
        """
        Initialize the CustomTestSuite.

        Arguments:

        id -- identifier for the suite, prepended to test cases.
        suite_settings -- settings overrides for this test suite.
        """
        unittest.TestSuite.__init__(self, tests)
        self.suite_settings = suite_settings or {}
        if id is None:
            mypath = os.path.abspath(
                sys.modules[CustomTestSuite.__module__].__file__)
            outerframes = inspect.getouterframes(inspect.currentframe())
            for outerframe in outerframes[1:]:
                if outerframe[3] != '__init__':
                    callerpath = outerframe[1]
                    if callerpath is None:
                        # It happens sometimes.  Why is a mystery.
                        callerpath = os.getcwd()
                    callerpath = os.path.abspath(callerpath)
                    break
            mydir, myname = os.path.split(mypath)
            if not mydir:
                mydir = os.curdir
            if callerpath.startswith(mydir):
                self.id = callerpath[len(mydir) + 1:] # caller's module
            else:
                self.id = callerpath
        else:
            self.id = id

    def addTestCase(self, test_case_class, method_name, input, expected,
                    id=None, run_in_debugger=0, **kwargs):
        """
        Create a CustomTestCase in the CustomTestSuite.
        Also return it, just in case.

        Arguments:

        test_case_class -- the CustomTestCase to add
        method_name -- a string; CustomTestCase.method_name is the test
        input -- input to the parser.
        expected -- expected output from the parser.
        id -- unique test identifier, used by the test framework.
        run_in_debugger -- if true, run this test under the pdb debugger.
        """
        if id is None:                  # generate id if required
            id = self.next_test_case_id
            self.next_test_case_id += 1
        # test identifier will become suiteid.testid
        tcid = '%s: %s' % (self.id, id)
        # suite_settings may be passed as a parameter;
        # if not, set from attribute:
        kwargs.setdefault('suite_settings', self.suite_settings)
        # generate and add test case
        tc = test_case_class(method_name, input, expected, tcid,
                             run_in_debugger=run_in_debugger, **kwargs)
        self.addTest(tc)
        return tc

    def generate_no_tests(self, *args, **kwargs):
        pass

class WriterPublishTestCase(CustomTestCase, docutils.SettingsSpec):

    """
    Test case for publish.
    """

    settings_default_overrides = {'_disable_config': 1,
                                  'strict_visitor': 1}
    writer_name = '' # set in subclasses or constructor

    def __init__(self, *args, **kwargs):
        if 'writer_name' in kwargs:
            self.writer_name = kwargs['writer_name']
            del kwargs['writer_name']
        CustomTestCase.__init__(self, *args, **kwargs)

    def test_publish(self):
        if self.run_in_debugger:
            pdb.set_trace()
        output = docutils.core.publish_string(
              source=self.input,
              reader_name='standalone',
              parser_name='restructuredtext',
              writer_name=self.writer_name,
              settings_spec=self,
              settings_overrides=self.suite_settings)
        self.compare_output(self.input, output, self.expected)


def exception_data(func, *args, **kwds):
    """
    Execute `func(*args, **kwds)` and return the resulting exception, the
    exception arguments, and the formatted exception string.
    """
    try:
        func(*args, **kwds)
    except Exception, detail:
        return (detail, detail.args,
                '%s: %s' % (detail.__class__.__name__, detail))


def _format_str(*args):
    r"""
    Return a tuple containing representations of all args.

    Same as map(repr, args) except that it returns multi-line
    representations for strings containing newlines, e.g.::

        '''\
        foo  \n\
        bar

        baz'''

    instead of::

        'foo  \nbar\n\nbaz'

    This is a helper function for CustomTestCase.
    """
    return_tuple = []
    for i in args:
        r = repr(i)
        if ( (isinstance(i, str) or isinstance(i, unicode))
             and '\n' in i):
            stripped = ''
            if isinstance(i, unicode) and r.startswith('u'):
                stripped = r[0]
                r = r[1:]
            elif isinstance(i, bytes) and r.startswith('b'):
                stripped = r[0]
                r = r[1:]
            # quote_char = "'" or '"'
            quote_char = r[0]
            assert quote_char in ("'", '"'), quote_char
            assert r[0] == r[-1]
            r = r[1:-1]
            r = (stripped + 3 * quote_char + '\\\n' +
                 re.sub(r'(?<!\\)((\\\\)*)\\n', r'\1\n', r) +
                 3 * quote_char)
            r = re.sub(r' \n', r' \\n\\\n', r)
        return_tuple.append(r)
    return tuple(return_tuple)
