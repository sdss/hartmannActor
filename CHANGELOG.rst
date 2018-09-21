.. _hartmannActor-changelog:

==========
Change Log
==========

.. _changelog-1.6.0:

1.6.0 (unreleased)
------------------

Added
^^^^^
* Ticket `#2867 <https://trac.sdss.org/ticket/2867>`_: implement bypass keyword to skip certain checks. For now only ``bypass="ffs"`` is accepted, which prevents a collimation to fail if the FFS keywords in the image header are badly formatted.

Code health
^^^^^^^^^^^
* ``Bumpversion`` version control.
* New version numbering scheme.
* Applied ``isort``, ``yapf``, and ``unify`` to all files.


.. _changelog-v1_5:

v1_5 (2017-06-11)
-----------------

Added
^^^^^
* Ticket `#2701 <https://trac.sdss.org/ticket/2701>`_: SOP Actions when hartmann fails on "gotoField". Adds a new keyword ``minBlueCorrection`` to ``collimate`` that will output only the minimum blue ring correction needed to get in focus tolerance. This is a necessary step for the changes in sopActor to address ticket #2701.

Fixed
^^^^^
* Ticket `#2705 <https://trac.sdss.org/ticket/2705>`_: SOP gotoField fails when no collimator move is required.
