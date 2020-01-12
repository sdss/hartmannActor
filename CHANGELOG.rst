.. _hartmannActor-changelog:

==========
Change Log
==========

.. _changelog-1.7.1:

1.7.1 (2020-01-12)
------------------

Added
^^^^^
* Implemented a ``hartmann abort`` command that allows to stop the collimate sequence. The ``Hartmann.collimate.__call__`` procedure is now run in a thread, which allows other commands to run while the collimation is progressing.


.. _changelog-1.7.0:

1.7.0 (2019-10-20)
------------------

Added
^^^^^
* Configuration option to define what cameras to use for adjusting focus. This can also be passed as comma-separated values to the keyword ``cameras`` (e.g., ``hartmann collimate cameras=b1,b1,b2``. If only one camera is available, only the collimator correction is calculated and applied (since we are optimising focus for a single camera it's not necessary to adjust both collimator and blue ring).


.. _changelog-1.6.2:

1.6.2 (2019-10-16)
------------------

Added
^^^^^
* Output spectrographs in use on ``status``.

Code health
^^^^^^^^^^^
* Move reading of spectrographs to use to ``HartmannActor`` and define an attribute there.


.. _changelog-1.6.1:

1.6.1 (2019-09-17)
------------------

Added
^^^^^
* New configuration option to set the available spectrographs.


.. _changelog-1.6.0:

1.6.0 (2018-09-26)
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
