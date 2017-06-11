.. _hartmannActor-changelog:

==========
Change Log
==========

This document records the main changes to the hartmannActor code.

.. _changelog-v1_5:
v1_5 (2017-06-11)
-----------------

Added
^^^^^
* Ticket `#2701 <https://trac.sdss.org/ticket/2701>`_: SOP Actions when hartmann fails on "gotoField". Adds a new keyword ``minBlueCorrection`` to ``collimate`` that will output only the minimum blue ring correction needed to get in focus tolerance. This is a necessary step for the changes in sopActor to address ticket #2701.

Fixed
^^^^^
* Ticket `#2705 <https://trac.sdss.org/ticket/2705>`_: SOP gotoField fails when no collimator move is required.

.. x.y.z (unreleased)
.. ------------------
..
.. A short description
..
.. Added
.. ^^^^^
.. * TBD
..
.. Changed
.. ^^^^^^^
.. * TBD
..
.. Fixed
.. ^^^^^
.. * TBD
