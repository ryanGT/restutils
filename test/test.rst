========
 A Test
========

Hello World
===========

Hello to all.

.. pyno::
   :echo: none

   from numpy import array
   from quantities import UnitQuantity,markup,set_default_units,kip,inch,ft,lbf,dimensionless
   markup.config.use_unicode = True
   set_default_units(length='in', mass='lb')
   ksi = UnitQuantity('ksi', kip/inch**2, symbol='ksi')	


.. py::

   x = 1.

.. py::

   a = array([[1,2,5],[3,4,4],[1,2,3]])

.. py::

   Nd = 3.6

.. py::

   Fy = 36*ksi

.. py:: 
   
   Fp = 1.8*Fy/Nd/1.2

