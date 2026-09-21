#!/usr/bin/env python3
import unittest

from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_pure_medium_v41 import CELLS


class CompressedMediumTest(unittest.TestCase):
    def test_fixed_three_stencils_and_read_only_probabilities(self):
        medium=CompressedResidualMedium(power=8);before=bytes(CELLS);digest=medium.digest();output=medium.predict_all(before)
        self.assertEqual(len(medium.projections),3);self.assertEqual((len(output),len(output[0]),len(output[0][0])),(4,CELLS,8));self.assertEqual(medium.digest(),digest)
    def test_action_renaming_remains_exact(self):
        before=bytes(CELLS);changed=bytes([1])+bytes(CELLS-1);a=CompressedResidualMedium(power=10);b=CompressedResidualMedium(power=10);rename=(3,2,0,1)
        for action in range(4):
            after=changed if action in (0,2) else before
            for _ in range(action+2):a.observe(before,action,after);b.observe(before,rename[action],after)
        for action in range(4):self.assertEqual(a.probability(before,action,0,0),b.probability(before,rename[action],0,0))


if __name__=='__main__':unittest.main()
