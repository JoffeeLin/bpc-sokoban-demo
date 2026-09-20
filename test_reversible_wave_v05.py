#!/usr/bin/env python3
"""Focused unit checks for experience-discovered reversible equivalence."""
from bpc_learned_wave_v04 import learn_raw_physics,parse,replay
from bpc_reversible_wave_v05 import discover_inverses,learned_reach,solve

LEVEL=parse('#####\n#@  #\n# $ #\n# . #\n#####')


def main():
    model,_,_,_=learn_raw_physics(40_404,3000,80)
    inverse,evidence=discover_inverses(50_505,600,60)
    assert inverse==(1,0,3,2)
    assert all(evidence[a][inverse[a]]>5000 for a in range(4))
    assert all(not value for a,row in enumerate(evidence) for b,value in enumerate(row) if b!=inverse[a])
    area,_=learned_reach(LEVEL,LEVEL.boxes,LEVEL.player,model,inverse)
    assert area.bit_count()==8
    result=solve(LEVEL,model,inverse); assert result['solved'] and replay(LEVEL,result['sequence'])[0]
    assert not solve(LEVEL,model,(2,3,0,1))['solved']
    print('V05_TESTS_PASS')


if __name__=='__main__':main()
