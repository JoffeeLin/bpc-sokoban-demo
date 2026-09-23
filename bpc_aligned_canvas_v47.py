#!/usr/bin/env python3
"""v0.47 camera: preserve the raw channels but align every row to 8 bytes."""
from bpc_pure_medium_v41 import CELLS,SIDE


def aligned_canvas(world):
    """External physical camera; x=7 and y=7 are explicit carrier padding."""
    image=bytearray([64])*CELLS
    for y in range(7):
        for x in range(7):
            inside=x<world.w and y<world.h;i=y*world.w+x if inside else -1
            image[y*SIDE+x]=(int(not inside or world.walls>>i&1)
                |(int(inside and i==world.agent)<<1)
                |(int(inside and world.objects>>i&1)<<2)
                |(int(inside and world.marks>>i&1)<<3)
                |(int(inside and world.switches>>i&1)<<4)
                |(int(inside and world.gates>>i&1)<<5))
    image[-1]=128|int(bool(world.marks))
    return bytes(image)
