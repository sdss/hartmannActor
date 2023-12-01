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

from clu.command import FakeCommand

from hartmann import CameraResult, Hartmann, HartmannCamera, HartmannResult, log
from hartmann.exceptions import HartmannError


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
        ("r2", 214, False),
    ],
)
def test_hartmann_camera(camera, piston, focused, config):
    im1 = get_image(244721, camera)
    im2 = get_image(244722, camera)

    hc = HartmannCamera("APO", camera, config=config)
    result = hc(im1, im2)

    assert isinstance(result, CameraResult)

    assert result.piston == piston
    assert result.focused is focused


@pytest.mark.parametrize("spec,move", [("sp1", -141), ("sp2", 473.0)])
async def test_hartmann_not_focused(spec, move, config):
    command = FakeCommand(log)

    hartmann = Hartmann("APO", spec, command=command, config=config)  # type: ignore

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


def test_hartmann_camera_reset(config):
    hc = HartmannCamera("APO", "b1", config=config)
    hc.reset()

    assert hc.observatory == "APO"
    assert hc.camera == "b1"
    assert hc.m is not None


def test_hartmann_camera_same_side_fails(config):
    im1 = get_image(244721, "b1")
    im2 = get_image(244721, "b1")

    hc = HartmannCamera("APO", "b1", config=config)

    with pytest.raises(HartmannError):
        hc(im1, im2)


def test_hartmann_camera_bad_ffs(caplog, config):
    img1 = get_image(268179, "b2")
    img2 = get_image(268180, "b2")

    hc = HartmannCamera("APO", "b2", config=config)

    with pytest.raises(HartmannError):
        hc(img1, img2)

    assert caplog.records[-1].levelname == "WARNING"
    assert "b2: failed reading FFS info" in caplog.text


def test_hartmann_camera_bad_Ne(caplog, config):
    img1 = get_image(169558, "r2", precooked=True)
    img2 = get_image(169559, "r2", precooked=True)

    hc = HartmannCamera("APO", "r2", config=config)

    with pytest.raises(HartmannError):
        hc(img1, img2)

    assert caplog.records[-1].levelname == "WARNING"
    assert "r2: 0 of 4 Ne lamps are on: 0 0 0 0" in caplog.text


def test_hartmann_camera_bad_HgCd(caplog, config):
    img1 = get_image(169560, "r2", precooked=True)
    img2 = get_image(169561, "r2", precooked=True)

    hc = HartmannCamera("APO", "r2", config=config)

    with pytest.raises(HartmannError):
        hc(img1, img2)

    assert caplog.records[-1].levelname == "WARNING"
    assert "r2: 0 of 4 HgCd lamps are on: 0 0 0 0" in caplog.text


def test_hartmann_camera_both_left(config):
    img1 = get_image(169552, "r2", precooked=True)
    img2 = get_image(169553, "r2", precooked=True)

    hc = HartmannCamera("APO", "r2", config=config)

    with pytest.raises(HartmannError):
        hc(img1, img2)


def test_hartmann_camera_command(caplog, config):
    command = FakeCommand(log)

    im1 = get_image(244721, "b1")
    im2 = get_image(244722, "b1")

    hc = HartmannCamera("APO", "b1", command=command, config=config)  # type: ignore
    result = hc(im1, im2)

    assert isinstance(result, CameraResult)

    assert "{'b1MeanOffset': [0.11, 'In Focus']}" in caplog.text
    assert "{'b1RingMove': -2.2}" in caplog.text
