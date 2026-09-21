#!/usr/bin/env python3
"""v0.42: resolve physical scales by parallel action-posterior separation."""
from bpc_pure_medium_v41 import ResidualMedium,contexts


class ParallelResidualMedium(ResidualMedium):
    def probability(self,image,action,cell,bit):
        if not self.use_action:return super().probability(image,action,cell,bit)
        estimates=[]
        for phase,context in enumerate(contexts(image,cell,self.projections)):
            means=[];variances=[]
            for alternative in range(4):
                address=self._address(phase,context,alternative,bit);z=self.zero[address];o=self.one[address];total=z+o+1
                means.append((o+.5)/total);variances.append((o+.5)*(z+.5)/(total*total*(total+1)))
            mean=sum(means)/4
            # Between-action posterior variance minus its exact sampling contribution.
            signal=max(0.,sum((p-mean)**2 for p in means)/4-3*sum(variances)/16)
            estimates.append((signal,means[action]))
        total=sum(weight for weight,_ in estimates)
        return sum(weight*p for weight,p in estimates)/total if total else super().probability(image,action,cell,bit)
