#!/usr/bin/env python3
"""GeneralBPC v7: sparse relational probability cubes for direct control.

The encoder receives only fixed-width raw binary voxel groups.  It discovers
low-frequency groups by occurrence count and emits translation-shared relation
keys.  Values are never assigned object names.  Two probability cubes learn
from reality: successful-action frequency and immediate raw-change frequency.
"""
from __future__ import annotations

import hashlib, math, pickle
from collections import Counter, defaultdict


def row12(): return [0]*12


class RelationalEncoder:
    def __init__(self, height=9, width=9, channels=6, radius=2, rarity=2,
                 high_order=False):
        self.h, self.w, self.c = height, width, channels
        self.radius, self.rarity, self.high_order = radius, rarity, high_order
        self.cache: dict[bytes, tuple[tuple, ...]] = {}

    def tokens(self, raw: bytes) -> tuple[int, ...]:
        return tuple(sum(raw[(i*self.c)+d] << d for d in range(self.c))
                     for i in range(self.h*self.w))

    def encode(self, raw: bytes) -> tuple[tuple, ...]:
        hit = self.cache.get(raw)
        if hit is not None: return hit
        t, out = self.tokens(raw), []
        count = Counter(t)
        rare = [(v, i%self.w, i//self.w) for i,v in enumerate(t) if count[v] <= self.rarity]
        rare.sort()  # Raw identity order only; no semantic role order.
        # Identity and all directed relative relations among rare raw groups.
        for lv,lx,ly in rare:
            out.append((0,lv))
            for rv,rx,ry in rare:
                out.append((1,lv,rv,rx-lx,ry-ly))
        # One anonymous configuration key preserves their joint geometry.
        if rare:
            ov,ox,oy = rare[0]
            out.append((2,tuple((v,x-ox,y-oy) for v,x,y in rare)))
        if self.high_order:
            patches={}
            for av,ax,ay in rare:
                patch=tuple(t[y*self.w+x] if 0<=x<self.w and 0<=y<self.h else -1
                            for y in range(ay-1,ay+2) for x in range(ax-1,ax+2))
                patches[(av,ax,ay)]=patch; out.append((5,av,patch))
                for direction,(sx,sy) in enumerate(((0,-1),(1,0),(0,1),(-1,0))):
                    ray=tuple(t[(ay+sy*k)*self.w+(ax+sx*k)]
                              if 0<=ax+sx*k<self.w and 0<=ay+sy*k<self.h else -1
                              for k in range(1,5))
                    out.append((6,av,direction,ray))
            for av,ax,ay in rare:
                for bv,bx,by in rare:
                    if (av,ax,ay)!=(bv,bx,by):
                        out.append((7,av,bv,bx-ax,by-ay,patches[(av,ax,ay)],patches[(bv,bx,by)]))
        # Atomic nearby matter and its conjunction with a second residue.
        for av,ax,ay in rare:
            for y in range(max(0,ay-self.radius),min(self.h,ay+self.radius+1)):
                for x in range(max(0,ax-self.radius),min(self.w,ax+self.radius+1)):
                    cell=t[y*self.w+x]; dx,dy=x-ax,y-ay
                    out.append((3,av,cell,dx,dy))
                    for bv,bx,by in rare:
                        if (bv,bx,by)!=(av,ax,ay):
                            out.append((4,av,bv,bx-ax,by-ay,cell,dx,dy))
        self.cache[raw] = tuple(out)
        return self.cache[raw]


class RelationalBPC:
    """Exact Beta/Dirichlet counts; no value function or reward score."""
    def __init__(self, encoder=None):
        self.encoder = encoder or RelationalEncoder()
        # row[0:4] = successful compact-path actions.  The remaining two
        # four-wide planes are Beta observations of whether an action changes
        # the raw frame: yes[4:8] / total[8:12].
        self.cube: dict[tuple, list[int]] = defaultdict(row12)
        self.success_prior, self.change_prior = [0]*4, [[0,0] for _ in range(4)]
        self.writes = 0

    def observe_transition(self, raw: bytes, action: int, changed: bool) -> None:
        self.change_prior[action][int(changed)] += 1
        self.writes += 1
        # Two independently addressable questions: raw pair offsets and joint
        # residue geometry.  No player/box/goal labels are supplied.
        for f in self.encoder.encode(raw):
            if f[0] in (1,2):
                row=self.cube[f]
                row[4+action] += int(changed)
                row[8+action] += 1
                self.writes += 1

    def observe_success(self, path: list[tuple[bytes,int]]) -> None:
        for raw,action in path:
            for f in self.encoder.encode(raw): self.cube[f][action] += 1
            self.success_prior[action] += 1; self.writes += 1

    def change_probabilities(self, raw: bytes) -> list[float]:
        """Calibrated Noul-like P(raw frame changes | relation, action)."""
        by_family={i:[] for i in (1,2)}
        for f in self.encoder.encode(raw):
            if f[0] in by_family:
                row=self.cube.get(f)
                if row is not None: by_family[f[0]].append(row)
        out=[]
        for action in range(4):
            no,yes=self.change_prior[action]
            channels=[math.log((yes+1)/(yes+no+2))]
            for rows in by_family.values():
                local=[]
                for row in rows:
                    total=row[8+action]
                    if total: local.append(math.log((row[4+action]+1)/(total+2)))
                if local: channels.append(sum(local)/len(local))
            out.append(math.exp(sum(channels)/len(channels)))
        return out

    def probabilities(self, raw: bytes, temperature=.72, families: set[int] | None = None,
                      use_change: bool = False) -> list[float]:
        by_family={i:[] for i in range(8 if self.encoder.high_order else 5)}
        for f in self.encoder.encode(raw):
            if families is not None and f[0] not in families: continue
            row=self.cube.get(f)
            if row is not None: by_family[f[0]].append(row)
        sp=sum(self.success_prior); prior=[(x+1)/(sp+4) for x in self.success_prior]
        logits=[math.log(x)*.12 for x in prior]
        family_logits=[]
        for kind,rows in by_family.items():
            if not rows: continue
            local=[0.,0.,0.,0.]; support=0.
            for row in rows:
                n=sum(row[:4])
                if n<3: continue
                p=[(row[a]+1)/(n+4) for a in range(4)]
                reliability=min(4.,math.log1p(n))
                for a in range(4): local[a]+=reliability*math.log(p[a])
                support+=reliability
            if support: family_logits.append([x/support for x in local])
        if family_logits:
            for a in range(4): logits[a]+=sum(x[a] for x in family_logits)/len(family_logits)
        # A separate calibrated question is combined only after its posterior
        # is computed.  This is Jev-inspired typed probability composition,
        # not a Jev implementation or a neural model.
        change=self.change_probabilities(raw)
        if use_change:
            for a in range(4): logits[a]+=.24*math.log(change[a])
        m=max(logits); q=[math.exp((x-m)/temperature) for x in logits]; z=sum(q)
        return [x/z for x in q]

    def decision(self, raw: bytes, temperature=.72, families: set[int] | None = None,
                 use_change: bool = False) -> dict:
        p=self.probabilities(raw,temperature,families,use_change)
        entropy=-sum(x*math.log(x) for x in p if x)
        return {"choice":p, "change":self.change_probabilities(raw),
                "confidence":1-entropy/math.log(4)}

    def rotated(self):
        cache=self.encoder.cache; self.encoder.cache={}
        try: m=pickle.loads(pickle.dumps(self,protocol=5))
        finally: self.encoder.cache=cache
        m.success_prior=m.success_prior[-1:]+m.success_prior[:-1]
        m.change_prior=m.change_prior[-1:]+m.change_prior[:-1]
        for row in m.cube.values():
            row[:4]=row[3:4]+row[:3]
            row[4:8]=row[7:8]+row[4:7]
            row[8:12]=row[11:12]+row[8:11]
        m.encoder.cache={}
        return m

    def digest(self):
        rows=[(repr(k),tuple(v)) for k,v in sorted(self.cube.items(),key=lambda x:repr(x[0]))]
        return hashlib.sha256(pickle.dumps((rows,self.success_prior,self.change_prior),protocol=5)).hexdigest()
