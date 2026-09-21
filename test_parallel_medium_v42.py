#!/usr/bin/env python3
import unittest

from bpc_parallel_medium_v42 import ParallelResidualMedium
from bpc_pure_medium_v41 import CELLS


class ParallelMediumTest(unittest.TestCase):
    def test_unobserved_output_is_probability_and_read_only(self):
        medium=ParallelResidualMedium(power=8);before=bytes(CELLS);snapshot=medium.digest();output=medium.predict_all(before)
        self.assertEqual((len(output),len(output[0]),len(output[0][0])),(4,CELLS,8));self.assertTrue(all(p==.5 for action in output for cell in action for p in cell));self.assertEqual(medium.digest(),snapshot)
    def test_real_writeback_separates_action_posteriors(self):
        medium=ParallelResidualMedium(power=10);before=bytes(CELLS);changed=bytes([1])+bytes(CELLS-1)
        for _ in range(8):medium.observe(before,0,changed);medium.observe(before,1,before);medium.observe(before,2,before);medium.observe(before,3,before)
        self.assertGreater(medium.probability(before,0,0,0),medium.probability(before,1,0,0))
    def test_action_renaming_is_exactly_equivariant(self):
        before=bytes(CELLS);changed=bytes([1])+bytes(CELLS-1);a=ParallelResidualMedium(power=10);b=ParallelResidualMedium(power=10);rename=(2,0,3,1)
        for action in range(4):
            after=changed if action in (0,3) else before
            for _ in range(action+2):a.observe(before,action,after);b.observe(before,rename[action],after)
        for action in range(4):self.assertEqual(a.probability(before,action,0,0),b.probability(before,rename[action],0,0))


if __name__=='__main__':unittest.main()
