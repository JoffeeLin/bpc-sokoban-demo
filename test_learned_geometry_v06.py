#!/usr/bin/env python3
"""Focused checks for learned anonymous macro geometry."""
import re
from pathlib import Path

from bpc_learned_geometry_v06 import audit_templates,learn_push_templates,solve
from bpc_learned_wave_v04 import learn_raw_physics,parse,replay
from bpc_reversible_wave_v05 import discover_inverses

LEVEL=parse('#####\n#@  #\n# $ #\n# . #\n#####')


def main():
    model,_,_,_=learn_raw_physics(40_404,3000,80);inverse,_=discover_inverses(50_505,600,60)
    templates,evidence,pushes=learn_push_templates(60_606,3000,80);rotated=tuple(templates[(a+1)%4] for a in range(4))
    assert pushes==4120 and all(len(row)==1 and row[0]['count']>900 for row in evidence)
    audit=audit_templates(templates,66_006,100,80);assert audit['exact']==audit['pushes']
    result=solve(LEVEL,model,inverse,templates);assert result['solved'] and replay(LEVEL,result['sequence'])[0]
    assert not solve(LEVEL,model,inverse,rotated)['solved']
    source=Path('bpc_learned_geometry_v06.py').read_text()
    assert not re.search(r'\bACTIONS\b|action\s*\^\s*1|\bmoved\s*\(',source)
    print('V06_TESTS_PASS')


if __name__=='__main__':main()
