#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-23
# @Filename: conftest.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pytest_asyncio

from clu.testing import setup_test_actor

from hartmann import config
from hartmann.actor import HartmannActor


@pytest_asyncio.fixture
async def actor():

    actor_ = HartmannActor.from_config(config, observatory="APO")
    await setup_test_actor(actor_)  # type: ignore

    yield actor_
