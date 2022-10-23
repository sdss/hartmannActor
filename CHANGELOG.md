# Changelog

## Next version

### 🚀 New

* Full refactor using CLU with support for LCO actors and hardware. Most of the functionality, commands, and keywords have not changed, but the calibration values are different because of the removal of the "fudge" factors.


## 2.0.2 (2022-01-07)

### 🔧 Fixed

* Using only `sp1` for now.


## 2.0.1 (2022-01-07)

### ✨ Improved

* Use `$ACTOR_LOG_DIR` and `$ACTOR_DAEMON_LOG_DIR` environment variables.


## 2.0.0 (2021-08-14)

### 🚀 New

* Modify to work with `actorcore>=5.0`, which includes modifications to be Python 3-only, change the location of the the configuration file, and proper packaging.


## 1.7.1 (2020-01-12)

### 🚀 New

* Implemented a `hartmann abort` command that allows to stop the collimate sequence. The `Hartmann.collimate.__call__` procedure is now run in a thread, which allows other commands to run while the collimation is progressing.


## 1.7.0 (2019-10-20)

### 🚀 New

* Configuration option to define what cameras to use for adjusting focus. This can also be passed as comma-separated values to the keyword `cameras` (e.g., `hartmann collimate cameras=b1,b1,b2`. If only one camera is available, only the collimator correction is calculated and applied (since we are optimising focus for a single camera it's not necessary to adjust both collimator and blue ring).


## 1.6.2 (2019-10-16)

### ✨ Improved

* Output spectrographs in use on `status`.

* 🧹 Cleanup

* Move reading of spectrographs to use to `HartmannActor` and define an attribute there.


## 1.6.1 (2019-09-17)

### 🚀 New

* New configuration option to set the available spectrographs.


## 1.6.0 (2018-09-26)

### 🚀 New

* Ticket [#2867](https://trac.sdss.org/ticket/2867): implement bypass keyword to skip certain checks. For now only `bypass="ffs"` is accepted, which prevents a collimation to fail if the FFS keywords in the image header are badly formatted.

### 🧹 Cleanup

* `Bumpversion` version control.
* New version numbering scheme.
* Applied `isort`, `yapf`, and `unify` to all files.


## v1_5 (2017-06-11)

### ✨ Improved

* Ticket [#2701](https://trac.sdss.org/ticket/2701): SOP Actions when hartmann fails on "gotoField". Adds a new keyword `minBlueCorrection` to `collimate` that will output only the minimum blue ring correction needed to get in focus tolerance. This is a necessary step for the changes in sopActor to address ticket #2701.

### 🔧 Fixed

* Ticket [#2705](https://trac.sdss.org/ticket/2705): SOP gotoField fails when no collimator move is required.
