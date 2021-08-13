"""General code for testing the hartmannActor."""

import unittest

from actorcore import TestHelper


class HartmannTester(TestHelper.ActorTester):
    def setUp(self):
        """Set up things that all hartmann tests need."""
        self.name = "hartmann"
        self.verbose = True
        # so we can call HartmannCmds.
        self.actor = TestHelper.FakeActor("hartmann", "hartmannActor")

        # If we've read in a list of cmd_calls for this class, prep them for use!
        if hasattr(self, "class_calls"):
            test_name = self.id().split(".")[-1]
            self.test_calls = self.class_calls.get(test_name, None)

        super(HartmannTester, self).setUp()
        self.actor.cmdr = self.cmd


class HartmannCallsTester(HartmannTester, unittest.TestCase):
    def __init__(self, *args, **kwargs):
        """Load up the cmd calls for this test class."""
        unittest.TestCase.__init__(self, *args, **kwargs)
        # -1 is the test function, -2 is test class, -3 (or 0) should be main
        class_name = self.id().split(".")[-2]
        self._load_cmd_calls(class_name)
        # lets us see really long list/list diffs
        self.maxDiff = None
