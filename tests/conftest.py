#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: conftest.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pathlib

import pytest
import pytest_asyncio

from clu.testing import setup_test_actor
from sdsstools import read_yaml_file

from hartmann.actor import HartmannActor


@pytest.fixture()
async def config():
    """Yields the test configuration file."""

    path = pathlib.Path(__file__).parent / "data/test_hartmann.yml"
    yield read_yaml_file(str(path))


@pytest_asyncio.fixture
async def actor(config):
    actor_ = HartmannActor.from_config(config, observatory="APO")
    await setup_test_actor(actor_)  # type: ignore

    yield actor_
