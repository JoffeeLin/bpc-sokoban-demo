#!/usr/bin/env python3
"""Anonymous delayed-closure physics used to test emergent carry."""
import random
from dataclasses import dataclass

from bpc_cross_task_v07 import ACTIONS


@dataclass(frozen=True)
class CarryWorld:
    cue:int;length:int;progress:int;visible:bool;decor:tuple
    @property
    def closed(self):return self.progress>=self.length
    def image(self):
        pixels=bytearray([64]*64)
        for y in range(7):
            for x in range(7):pixels[y*8+x]=int(x in (0,6) or y in (0,6))
        for cell,bit in self.decor:pixels[cell]|=bit
        center=3*8+3;pixels[center]|=2
        if self.visible:
            dx,dy=ACTIONS[self.cue];pixels[(3+dy)*8+3+dx]|=8
        pixels[-1]=128|int(not self.closed);return bytes(pixels)
    def step(self,action):
        progress=self.progress+(action==self.cue and not self.closed)
        return CarryWorld(self.cue,self.length,progress,self.visible and action!=self.cue,self.decor)
    def signature(self):return self.cue,self.length,self.decor


def world(rng,cue,length):
    reserved={3*8+3,(3+ACTIONS[cue][1])*8+3+ACTIONS[cue][0]};cells=[y*8+x for y in range(1,6) for x in range(1,6) if y*8+x not in reserved];rng.shuffle(cells)
    decor=tuple(sorted((cell,rng.choice((1,4,16,32))) for cell in cells[:rng.randrange(1,8)]))
    return CarryWorld(cue,length,0,True,decor)


def suite(seed,count,lengths,exclude=()):
    rng=random.Random(seed);exclude=set(exclude);seen=set();out=[];attempts=0
    while len(out)<count:
        attempts+=1;cue=len(out)%4;item=world(rng,cue,rng.choice(tuple(lengths)));signature=item.signature()
        if signature in exclude or signature in seen:continue
        seen.add(signature);out.append(item)
    return out,seen,attempts
