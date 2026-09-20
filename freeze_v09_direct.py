#!/usr/bin/env python3
"""Create the v0.9 direct-composition holdout before any frozen evaluation."""
import json
from pathlib import Path

from bpc_direct_composition_v09 import generate_holdout

ROOT=Path(__file__).resolve().parent


def main():
    holdout,attempts=generate_holdout(99_209,16)
    rows=[{'h':world.h,'w':world.w,'walls':world.walls,'agent':world.agent,'objects':world.objects,
           'marks':world.marks,'shortest':distance} for world,distance in holdout]
    output={'format':'bpc-direct-composition-v09-holdout','seed':99209,'attempts':attempts,'worlds':rows}
    path=ROOT/'holdout_v09.json';path.write_text(json.dumps(output,indent=2)+'\n');print(path);print(json.dumps(output,indent=2))


if __name__=='__main__':main()
