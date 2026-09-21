#!/usr/bin/env python3
"""v0.44: parallel posterior medium without exact 3x3 context memory."""
from bpc_parallel_medium_v42 import ParallelResidualMedium
from bpc_pure_medium_v41 import PROJECTIONS


class CompressedResidualMedium(ParallelResidualMedium):
    def __init__(self,power=20,use_action=True):super().__init__(power,use_action,PROJECTIONS[:3])
