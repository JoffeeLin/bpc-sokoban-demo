#!/usr/bin/env python3
"""Development reproduction of learned local physics plus v0.3 wave shell."""
from __future__ import annotations

import json,time

from bpc_learned_wave_v04 import learn_raw_physics,parse,solve,validate_physics

MAPS={
"one":"""#######
#     #
#     #
# @$. #
#     #
#     #
#######""",
"old_l1":"""#######
#     #
# @   #
#  $  #
#   . #
#     #
#######""",
"irregular2":"""#########
#   .   #
#       #
# . $   #
#  $@   #
#       #
#########""",
"irregular3":"""##########
# . # .  #
#   #    #
# $   $  #
#   $ .  #
#   @    #
##########""",
"boxes5":"""#############
#           #
# . . . . . #
# $ $ $ $ $ #
#     @     #
#           #
#############""",
"boxes6":"""###############
#             #
# . . . . . . #
# $ $ $ $ $ $ #
#      @      #
#             #
###############"""}


def main():
    started=time.perf_counter()
    full,no_far,experience,manifest=learn_raw_physics(40_404,3000,80)
    validation={"full":validate_physics(full,90_901,500,80),
                "no_far":validate_physics(no_far,90_901,500,80)}
    solved={}
    for name,text in MAPS.items():
        before=time.perf_counter(); solved[name]=solve(parse(text),full)
        solved[name]["seconds"]=time.perf_counter()-before
    result={"development_only":True,"model":"raw three-cell exact probability cube + v0.3 configuration wave",
        "training_experience":experience,"training_manifest":manifest,
        "learned_rows":len(full.rows),"model_sha256":full.digest(),
        "validation":validation,"levels":solved,"seconds":time.perf_counter()-started,
        "boundary":"Local Sokoban transitions are learned from raw random experience. Reachable-component compression, macro candidate geometry, terminal seeding, and backward wave are still supplied."}
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
