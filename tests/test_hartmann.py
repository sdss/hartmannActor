#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: test_hartmann.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pathlib

from hartmann import CameraResult, HartmannCamera


def get_image(image_no: int, camera: str = "b1", precooked: bool = False):

    data = pathlib.Path(__file__).parent / "data"

    if precooked:
        data = data / "precooked"
    else:
        data = data / "downloaded"

    filename = f"sdR-{camera}-{image_no:08}.fit.gz"

    path = data / filename

    if not path.exists():
        raise FileExistsError(f"File {path!s} does not exist.")

    return path


async def test_hartmann_camera():

    im1 = get_image(244721, "b1")
    im2 = get_image(244722, "b1")

    hc = HartmannCamera("APO", "b1")
    result = hc(im1, im2)

    assert isinstance(result, CameraResult)
