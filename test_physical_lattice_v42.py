#!/usr/bin/env python3
import random,unittest

from physical_lattice_v42 import CELLS,random_lattice,step_lattice


class PhysicalLatticeTest(unittest.TestCase):
    def test_boundary_and_reproducibility(self):
        a=random_lattice(random.Random(7),.1,.2);b=random_lattice(random.Random(7),.1,.2)
        self.assertEqual(a,b);self.assertEqual(len(a),CELLS)
        self.assertTrue(all(a[y*8+x]&1 for y in range(8) for x in range(8) if x in (0,7) or y in (0,7)))
    def test_particles_move_simultaneously_and_walls_persist(self):
        state=bytearray([0]*CELLS)
        for y in range(8):
            for x in range(8):
                if x in (0,7) or y in (0,7):state[y*8+x]=1
        state[3*8+2]=2;state[3*8+3]=2;state[3*8+5]=1
        after=step_lattice(bytes(state),1)
        self.assertTrue(after[3*8+2]&2);self.assertFalse(after[3*8+3]&2);self.assertTrue(after[3*8+4]&2);self.assertEqual(bytes(v&1 for v in state),bytes(v&1 for v in after))


if __name__=='__main__':unittest.main()
