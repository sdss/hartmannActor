#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: test_hartmann.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pathlib

import pytest

from hartmann import CameraResult, Hartmann, HartmannCamera, HartmannResult


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


@pytest.mark.parametrize(
    "camera,piston,focused",
    [
        ("b1", 707, True),
        ("r2", 3471, False),
    ],
)
async def test_hartmann_camera(camera, piston, focused):

    im1 = get_image(244721, camera)
    im2 = get_image(244722, camera)

    hc = HartmannCamera("APO", camera)
    result = hc(im1, im2)

    assert isinstance(result, CameraResult)

    assert result.piston == piston
    assert result.focused is focused


@pytest.mark.parametrize("spec,move", [("sp1", -141), ("sp2", 3311.5)])
async def test_hartmann_not_focused(spec, move):

    hartmann = Hartmann("APO", spec)

    spec_id = spec[-1]

    images = [
        get_image(244721, "b" + spec_id),
        get_image(244721, "r" + spec_id),
        get_image(244722, "b" + spec_id),
        get_image(244722, "r" + spec_id),
    ]

    result = await hartmann.collimate(images)

    assert isinstance(result, HartmannResult)
    assert result.move == move
