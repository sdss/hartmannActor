#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-28
# @Filename: hub.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

# type: ignore


KeysDictionary(
    'hub', (2, 0),
    Key('actors', String() * (0,), help='Current actors'),
    Key('commanders', String() * (0,), help='Current commanders'),
    Key('user', String() * (5, 6),
        help="""Information about a user:
                - cmdrID (program.name)
                - client name (e.g. "TUI")
                - client version (sortable)
                - system info (e.g. platform.platform())
                - IP address (numeric)
                ? fully qualified domain name (if supplied)
        """,
        doCache=False,
        refreshCmd='status'),
    Key('text', String(),
        help="Craig's random musings", doCache=False),
    Key('users', String() * (0,),
        help='current human (non-hub) commanders'),
    Key('version', String(),
        help="Craig's random choice of version string"),
    Key('httpRoot', String() * 2,
        help='hostname and root directory for images'),
    Key('CmdIn', String(),
        help='Who sent the command?'),
    Key('NoTarget', String(),
        help='Which command target was not found?'),
    Key('hubtxt', String()),
)
