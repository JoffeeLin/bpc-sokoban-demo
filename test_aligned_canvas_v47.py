#!/usr/bin/env python3
import unittest

from bpc_aligned_canvas_v47 import aligned_canvas
from bpc_fourth_factor_v28 import _world
from bpc_pure_medium_v41 import PROJECTIONS,local


class AlignedCanvasTest(unittest.TestCase):
    def test_world_coordinates_map_to_eight_wide_rows(self):
        world=_world((2,3),((4,2),),((5,2),),switches=((1,1),),gates=((3,3),))
        image=aligned_canvas(world)
        self.assertEqual(len(image),64)
        self.assertEqual(image[3*8+2]&2,2)
        self.assertEqual(image[2*8+4]&4,4)
        self.assertEqual(image[2*8+5]&8,8)
        self.assertEqual(image[1*8+1]&16,16)
        self.assertEqual(image[3*8+3]&32,32)

    def test_padding_and_port_are_explicit(self):
        world=_world((1,1),(),())
        image=aligned_canvas(world)
        self.assertTrue(all(image[y*8+7]==64 for y in range(7)))
        self.assertTrue(all(image[7*8+x]==64 for x in range(7)))
        self.assertEqual(image[63],128)
        marked=_world((1,1),(),((2,2),))
        self.assertEqual(aligned_canvas(marked)[63],129)

    def test_local_axes_are_actual_board_neighbors(self):
        world=_world((3,3),((3,2),),((4,3),))
        image=aligned_canvas(world);cell=3*8+3
        horizontal=local(image,cell,PROJECTIONS[1]);vertical=local(image,cell,PROJECTIONS[2])
        self.assertEqual(horizontal,bytes((image[cell-1],image[cell],image[cell+1])))
        self.assertEqual(vertical,bytes((image[cell-8],image[cell],image[cell+8])))
        self.assertEqual(horizontal[2]&8,8)
        self.assertEqual(vertical[0]&4,4)

    def test_physical_rotation_moves_pixels_to_rotated_coordinates(self):
        base=_world((1,2),((4,2),),((5,4),),switches=((2,4),),gates=((3,1),),walls=((2,2),),transform=0)
        rotated=_world((1,2),((4,2),),((5,4),),switches=((2,4),),gates=((3,1),),walls=((2,2),),transform=1)
        a,b=aligned_canvas(base),aligned_canvas(rotated)
        for y in range(7):
            for x in range(7):self.assertEqual(a[y*8+x],b[x*8+(6-y)])


if __name__=='__main__':unittest.main()
