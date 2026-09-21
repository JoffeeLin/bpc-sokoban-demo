#!/usr/bin/env python3
"""Pure BPC v0.41: one fixed probability medium for reality residuals."""
import hashlib

SIDE=8;CELLS=SIDE*SIDE;BITS=8;MASK64=(1<<64)-1
PROJECTIONS=((0,),(-1,0,1),(-SIDE,0,SIDE),(-SIDE-1,-SIDE,-SIDE+1,-1,0,1,SIDE-1,SIDE,SIDE+1))
OFFSETS={-SIDE-1:(-1,-1),-SIDE:(-1,0),-SIDE+1:(-1,1),-1:(0,-1),0:(0,0),1:(0,1),SIDE-1:(1,-1),SIDE:(1,0),SIDE+1:(1,1)}


def canvas(world):
    """External camera: anonymous packed pixels plus one minimal open boundary."""
    pixels=[]
    for y in range(7):
        for x in range(7):
            i=y*world.w+x if x<world.w and y<world.h else -1
            pixels.append((int(i<0 or world.walls>>i&1))|(int(i==world.agent)<<1)|(int(i>=0 and world.objects>>i&1)<<2)|(int(i>=0 and world.marks>>i&1)<<3)|(int(i>=0 and world.switches>>i&1)<<4)|(int(i>=0 and world.gates>>i&1)<<5))
    # 64/128 are physical port-carrier bits: no sensor and closure port, not task semantics.
    return bytes(pixels+[64]*(CELLS-len(pixels)-1)+[128|int(bool(world.marks))])


def local(canvas_,cell,offsets):
    y,x=divmod(cell,SIDE);out=[]
    for offset in offsets:
        dy,dx=OFFSETS[offset] # Uniform physical neighborhood, never a task role.
        yy,xx=y+dy,x+dx;out.append(canvas_[yy*SIDE+xx] if 0<=yy<SIDE and 0<=xx<SIDE else 0)
    return bytes(out)


def contexts(canvas_,cell,projections=PROJECTIONS):return tuple(local(canvas_,cell,offsets) for offsets in projections)


class ResidualMedium:
    """All predicted bits interfere in the same fixed-capacity Beta medium."""
    def __init__(self,power=20,use_action=True,projections=PROJECTIONS):
        self.size=1<<power;self.mask=self.size-1;self.zero=bytearray(self.size);self.one=bytearray(self.size);self.use_action=use_action;self.projections=projections;self.writes=0
    @staticmethod
    def _mix(value,byte):return ((value^byte)*1099511628211)&MASK64
    def _address(self,phase,context,action,bit):
        value=1469598103934665603
        for item in (phase,bit,*context):value=self._mix(value,item+1)
        # Anonymous actions occupy exchangeable equal regions; renaming them only permutes regions.
        return (((value&(self.size//4-1))<<2)|action) if self.use_action else value&self.mask
    def probability(self,canvas_,action,cell,bit):
        zero=one=0
        for phase,context in enumerate(contexts(canvas_,cell,self.projections)):
            address=self._address(phase,context,action,bit);zero+=self.zero[address];one+=self.one[address]
        return (one+.5)/(zero+one+1)
    def predict(self,canvas_,action):return [[self.probability(canvas_,action,cell,bit) for bit in range(BITS)] for cell in range(CELLS)]
    def predict_all(self,canvas_):return tuple(self.predict(canvas_,action) for action in range(4))
    def observe(self,before,action,after):
        for cell in range(CELLS):
            rows=contexts(before,cell,self.projections);target=after[cell]
            for bit in range(BITS):
                value=(target>>bit)&1
                for phase,context in enumerate(rows):
                    address=self._address(phase,context,action,bit);row=self.one if value else self.zero
                    if row[address]<255:row[address]+=1
                    self.writes+=1
    def active_cells(self):return sum(bool(a or b) for a,b in zip(self.zero,self.one))
    def digest(self):return hashlib.sha256(bytes(self.zero)+bytes(self.one)).hexdigest()


def defined_bits():return tuple((cell,bit) for cell in range(49) for bit in range(6))+((63,0),)
