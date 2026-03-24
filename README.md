# hartmannActor

![Versions](https://img.shields.io/badge/python->=3.11-blue)
[![Test](https://github.com/sdss/hartmannActor/actions/workflows/test.yml/badge.svg)](https://github.com/sdss/hartmannActor/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/sdss/hartmannActor/branch/main/graph/badge.svg)](https://codecov.io/gh/sdss/hartmannActor)

The `hartmann` actor is responsible for taking and analysing Hartmann door exposures to determine the optimal focus for the BOSS spectrographs at APO and LCO (sp1 and sp2, respectively). It also commands the spectrograph collimator motors to adjust the focus.

## Procedure

The `hartmann` actor performs the following steps:

- Turns on the appropriate arc lamps and waits for them to warm up.
- Takes two BOSS exposures, each one with a different Hartmann door closed (left and right). For a perfectly focused system, the exposures would be identical. As spectrograph focus degrades, the position of the spectral lines in one of the Hartmann images shifts vertically with respect to the other. The shift is proportional to the amount of defocus, which can be corrected by either adjusting the collimator position or the position of the blue or red cameras via the camera "rings". In practice only ring needs to be adjusted, with the other camera being the reference one and its focus optimised by the collimator. The blue ring/camera is the one that is adjusted.
- The images are analysed to determine the vertical shift. This is done by applying vertical shifts to one of the images and computing the product of both images. The product will be maximised when the vertical shift is correct. A calibration is applied to convert the vertical shift to a collimator movement.
- If the collimator can correct the focus for both cameras, within a tolerance, the collimator is moved that amount. Otherwise, the necessary ring movement is computed and the user is instructed to move the blue ring by that amount and rerun the `hartmann collimate` command.

## Usage

See `hartmann --help` for usage instructions. In general the `hartmann collimate` command runs the entire sequence. `--no-move` can be used to run the sequence without moving the collimator. Other flags such as `--exposure-time` or `--ignore-residuals` can be used to change the command behaviour.

## Code style and development

`hartmannActor` uses [uv](https://github.com/astral-sh/uv) for package and dependency management, and [ruff](https://github.com/astral-sh/ruff) for code style enforcement. [ty](https://github.com/astral-sh/ty) is the recommended type checker. See `pyproject.toml` for configuration details.
