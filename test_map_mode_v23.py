#!/usr/bin/env python3
import unittest
from bpc_map_mode_v23 import hard


class MapModeTest(unittest.TestCase):
    def test_map_is_deterministic_and_normalized(self):
        self.assertEqual(hard((.49,.51)),(0.,1.));self.assertEqual(hard((.5,.5)),(1.,0.));self.assertEqual(sum(hard((.2,.8))),1.)


if __name__=='__main__':unittest.main()
