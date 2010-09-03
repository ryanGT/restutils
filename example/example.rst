===================
 ReSTutils Example
===================

.. role:: ref

.. raw::  latex

  \newcommand*{\docutilsroleref}{\ref}

:Author: Bill Purcell
:Date: Sometime in the distant future.

python-numpy
============

.. pyno::
   :echo: none

   from numpy import *	

.. py::
   :label: eq1

   a = array([[1,2,3],[4,5,6],[7,8,9]])


From :ref:`eq1` you can see something spectacular.

.. py::

   b = arange(0,5,.01)

..
  I can't do more than 10 elements in a 2D array withouth using
  \setcounter to set MaxMatrixCols.

.. py::

   c = array([[1]*10]*10)



