#!/usr/bin/env python3
"""v0.49: one task-agnostic decaying activity field in the same BPC medium."""
import hashlib,struct

from bpc_port_interference_v45 import PortInterferenceMedium


class ResidualActivityMedium(PortInterferenceMedium):
    """Physical addresses stay active briefly; later reality writes through them."""
    def __init__(self,power=20,use_action=True,decay=.82):
        super().__init__(power,use_action);self.decay=decay;self.activity={};self.mode='normal';self.memoryless=False
    def begin(self,mode='normal',memoryless=False):self.activity={};self.mode=mode;self.memoryless=memoryless
    def _addresses(self,image,action):return tuple(self._port_address(phase,context,action if self.use_action else 0,0) for phase,context in self._features(image))
    def _read_action(self,action):
        if self.mode=='zero':return None
        if self.mode=='shift':return (action+1)%4
        return action
    def probability(self,image,action,cell,bit):
        base=super().probability(image,action,cell,bit)
        if not image[cell]&128 or bit!=0:return base
        read=self._read_action(action)
        if read is None:return base
        rows=[]
        for address,strength in self.activity.items():
            if self.use_action and address&3!=read:continue
            z=self.zero[address];o=self.one[address];value=(o+.5)/(z+o+1)
            rows.append((strength,min(1.,max(0.,2*base-value)) if self.mode=='flip' else value))
        total=sum(weight for weight,_ in rows)
        return (base+sum(weight*p for weight,p in rows))/(1+total)
    def advance(self,before,action,after,learn=False):
        """Advance volatile physics; persistent writeback occurs only in learning."""
        current=self._addresses(before,action);target=after[-1]&1;prediction=self.probability(before,action,len(before)-1,0)
        if learn:
            super().observe(before,action,after);row=self.one if target else self.zero
            for address,strength in self.activity.items():
                if self.use_action and address&3!=action:continue
                # Only prediction/reality residual writes back through lingering activity.
                repeats=int(round(strength*abs(target-prediction)*4))
                for _ in range(repeats):
                    if row[address]<255:row[address]+=1
                    self.writes+=1
        if self.memoryless:self.activity={};return
        self.activity={address:value*self.decay for address,value in self.activity.items() if value*self.decay>=.08}
        for address in current:self.activity[address]=min(4.,self.activity.get(address,0.)+1.)
    def activity_digest(self):
        packed=b''.join(struct.pack('<If',address,value) for address,value in sorted(self.activity.items()))
        return hashlib.sha256(packed).hexdigest()
