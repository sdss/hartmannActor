#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-08-07
# @Filename: test_actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pytest

from hartmann import config
from hartmann.actor import HartmannActor
from hartmann.exceptions import HartmannError


async def test_actor(actor):

    assert isinstance(actor, HartmannActor)


async def test_actor_no_observatory(monkeypatch):

    monkeypatch.delenv("OBSERVATORY", raising=False)

    with pytest.raises(HartmannError):
        HartmannActor.from_config(config, observatory=None)
