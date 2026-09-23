#!/usr/bin/env python3
"""v0.45: task-independent global interference into physical data ports."""
from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_pure_medium_v41 import contexts


class PortInterferenceMedium(CompressedResidualMedium):
    """Bytes with carrier bit 7 are physical one-bit ports."""
    def _features(self,image):
        for source,value in enumerate(image):
            if value<64:
                for phase,context in enumerate(contexts(image,source,self.projections)):
                    yield phase,context
    def _port_address(self,phase,context,action,bit):return self._address(phase+len(self.projections),b'\xc1'+context,action,bit)
    def probability(self,image,action,cell,bit):
        if not image[cell]&128 or bit!=0:return super().probability(image,action,cell,bit)
        rows=[];fallback_zero=fallback_one=0
        for phase,context in self._features(image):
            means=[];variances=[]
            for alternative in range(4):
                address=self._port_address(phase,context,alternative,bit);z=self.zero[address];o=self.one[address];total=z+o+1
                means.append((o+.5)/total);variances.append((o+.5)*(z+.5)/(total*total*(total+1)))
                if alternative==(action if self.use_action else 0):fallback_zero+=z;fallback_one+=o
            mean=sum(means)/4;signal=max(0.,sum((p-mean)**2 for p in means)/4-3*sum(variances)/16) if self.use_action else 0.
            rows.append((signal,means[action]))
        total=sum(weight for weight,_ in rows)
        return sum(weight*p for weight,p in rows)/total if total else (fallback_one+.5)/(fallback_zero+fallback_one+1)
    def observe(self,before,action,after):
        super().observe(before,action,after);features=tuple(self._features(before))
        for cell,value in enumerate(before):
            if not value&128:continue
            target=after[cell]
            bit=0;row=self.one if target&1 else self.zero
            for phase,context in features:
                address=self._port_address(phase,context,action if self.use_action else 0,bit)
                if row[address]<255:row[address]+=1
                self.writes+=1
