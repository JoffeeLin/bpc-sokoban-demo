#!/usr/bin/env python3
"""Render an English evidence video from real v0.44 model predictions."""
import random,subprocess,tempfile
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_compressed_medium_v44 import CompressedResidualMedium
from bpc_fourth_factor_v28 import step
from bpc_pure_medium_v41 import canvas
from bpc_temporal_cross_generator_v33 import generate
from bpc_three_factor_v12 import key
from experiment_v41_pure_medium_dev import holdout_rows,training_rows
from experiment_v42_parallel_posterior_dev import fresh_training
from experiment_v43_causal_lattice import rows as lattice_rows
from physical_causal_lattice_v43 import random_lattice,step_lattice

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v44compressed';W,H=1280,720
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'


def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def train(rows):
    medium=CompressedResidualMedium()
    for before,action,after in rows:medium.observe(before,action,after)
    return medium
def hard(prediction):return bytes(sum((p>=.5)<<bit for bit,p in enumerate(cell)) for cell in prediction)


def grid(draw,state,x,y,size,cells,domain,previous=None):
    unit=size/cells
    for index,value in enumerate(state[:cells*cells]):
        yy,xx=divmod(index,cells);box=(int(x+xx*unit),int(y+yy*unit),int(x+(xx+1)*unit-2),int(y+(yy+1)*unit-2))
        if domain=='sokoban':
            color='#26334a' if value&1 else '#101722';draw.rounded_rectangle(box,3,fill=color)
            if value&8:draw.ellipse((box[0]+unit*.36,box[1]+unit*.36,box[0]+unit*.64,box[1]+unit*.64),fill='#f6c85f')
            if value&16:draw.rectangle((box[0]+unit*.28,box[1]+unit*.28,box[0]+unit*.72,box[1]+unit*.72),outline='#a78bfa',width=2)
            if value&32:draw.line((box[0]+4,box[1]+4,box[2]-4,box[3]-4),fill='#38bdf8',width=3)
            if value&4:draw.rounded_rectangle((box[0]+unit*.18,box[1]+unit*.18,box[0]+unit*.82,box[1]+unit*.82),3,fill='#f59e0b')
            if value&2:draw.ellipse((box[0]+unit*.18,box[1]+unit*.18,box[0]+unit*.82,box[1]+unit*.82),fill='#34d399')
        else:
            color='#0f3d4f' if value&4 else '#172033';draw.rounded_rectangle(box,3,fill='#465163' if value&1 else color)
            if value&2:draw.ellipse((box[0]+unit*.2,box[1]+unit*.2,box[0]+unit*.8,box[1]+unit*.8),fill='#facc15')
        if previous is not None and index<len(previous) and value!=previous[index]:draw.rounded_rectangle(box,3,outline='#fb7185',width=3)


def panel(draw,x,title,subtitle,current,predicted,actual,cells,domain,action,step_no):
    draw.rounded_rectangle((x,82,x+610,642),18,fill='#0d1422',outline='#26364f',width=2);draw.text((x+22,102),title,font=font(25,True),fill='#f8fafc');draw.text((x+22,137),subtitle,font=font(15),fill='#93c5fd')
    labels=('CURRENT','BPC PREDICTED NEXT','ACTUAL NEXT');positions=(x+24,x+221,x+418)
    for label,px in zip(labels,positions):draw.text((px,172),label,font=font(13,True),fill='#94a3b8')
    grid(draw,current,positions[0],198,166,cells,domain);grid(draw,predicted,positions[1],198,166,cells,domain,current);grid(draw,actual,positions[2],198,166,cells,domain,current)
    draw.text((x+22,390),f'Step {step_no:02d}/14   •   Action: {action}',font=font(21,True),fill='#e2e8f0')
    if domain=='sokoban':lines=('Frozen unseen-context Brier: 0.2314','40.28% full contexts unseen','10,885 active cells  •  91.84% lower occupancy')
    else:lines=('Frozen unseen-context Brier: 0.0417','55.90% full contexts unseen','14,000 active cells  •  terrain-flip control +95.40%')
    for i,line in enumerate(lines):draw.text((x+22,438+i*35),line,font=font(18 if i==0 else 17),fill='#dbeafe' if i==0 else '#a7f3d0')
    draw.text((x+22,560),'Red outline = real or predicted changed cell',font=font(14),fill='#fda4af')


def scene(sok,lattice,index):
    image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image);draw.text((32,20),'Pure BPC v0.44  •  Compact Physical Prediction',font=font(31,True),fill='#f8fafc');draw.text((942,29),'FROZEN FIRST RUN',font=font(17,True),fill='#34d399')
    s=sok[index];l=lattice[index];panel(draw,20,'DOMAIN A — SOKOBAN PHYSICS','Anonymous pixels + anonymous action',s[0],s[1],s[2],7,'sokoban',s[3],index+1);panel(draw,650,'DOMAIN B — CAUSAL PARTICLE FIELD','Same core; fresh probability state',l[0],l[1],l[2],8,'lattice',l[3],index+1)
    draw.text((W//2,681),'No neural network  •  No reward  •  No planner  •  World prediction only — not goal solving or AGI',anchor='mm',font=font(17,True),fill='#cbd5e1');return image


def title_frame(outro=False):
    image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image);draw.rounded_rectangle((105,85,1175,635),28,fill='#0d1422',outline='#2b466b',width=3)
    draw.text((W//2,145),'PURE BPC v0.44',anchor='mm',font=font(54,True),fill='#f8fafc');draw.text((W//2,215),'Compact physical prediction across two domains',anchor='mm',font=font(30),fill='#93c5fd')
    if not outro:
        draw.text((W//2,306),'One fixed non-neural probability core',anchor='mm',font=font(26,True),fill='#34d399');draw.text((W//2,357),'40.28% / 55.90% unseen local contexts',anchor='mm',font=font(25),fill='#e2e8f0');draw.text((W//2,401),'91.84% / 97.84% lower active occupancy',anchor='mm',font=font(25),fill='#e2e8f0');draw.text((W//2,485),'Frozen before execution • causal controls • zero evaluation writes',anchor='mm',font=font(21),fill='#a7f3d0')
    else:
        draw.text((W//2,320),'Source + preregistration + raw evidence',anchor='mm',font=font(28,True),fill='#34d399');draw.text((W//2,380),'github.com/JoffeeLin/bpc-sokoban-demo',anchor='mm',font=font(26),fill='#bfdbfe');draw.text((W//2,470),'Boundary: physical prediction only — not goal solving, weight transfer, or AGI',anchor='mm',font=font(19),fill='#fda4af')
    return image


def traces():
    _,v41,_,_=training_rows(241010);_,suite,_=holdout_rows(241110,v41);old=set(v41)|{key(w) for _,w,_ in suite};_,v42,_,_,_=fresh_training(242010,old);_,suite,_=holdout_rows(242110,old|v42);old|=v42|{key(w) for _,w,_ in suite};_,vf,_,_,_=fresh_training(243010,old);_,suite,_=holdout_rows(243110,old|vf);old|=vf|{key(w) for _,w,_ in suite};srows,sinitials,_,_,_=fresh_training(245010,old);sm=train(srows);demo,_=generate(246110,1,old|sinitials);world=demo[0][1];srng=random.Random(246111);sout=[];snames=('LEFT','RIGHT','UP','DOWN')
    _,p1,_,_,_=lattice_rows(43001,120,1,24);_,p2,_,_,_=lattice_rows(43002,24,4,24,True,p1);lold=p1|p2;_,d1,_,_,_=lattice_rows(244020,120,1,24,False,lold);_,d2,_,_,_=lattice_rows(244120,24,4,24,True,lold|d1);lold|=d1|d2;lrows,linitials,_,_,_=lattice_rows(245020,120,1,24,False,lold);lm=train(lrows);lrng=random.Random(246120);state=random_lattice(lrng,.18,.24,.63);an=random.Random(246121);lout=[];lnames=('UP','RIGHT','DOWN','LEFT')
    for _ in range(14):
        action=srng.randrange(4);before=canvas(world);after_world=step(world,action);actual=canvas(after_world);sout.append((before[:49],hard(sm.predict(before,action))[:49],actual[:49],snames[action]));world=after_world
        action=an.randrange(4);actual=step_lattice(state,action);lout.append((state,hard(lm.predict(state,action)),actual,lnames[action]));state=actual
    return sout,lout


def main():
    OUT.mkdir(parents=True,exist_ok=True);sok,lattice=traces();stills=[title_frame()]+[scene(sok,lattice,i) for i in range(14)]+[title_frame(True)];stills[6].save(OUT/'poster_v44_compressed.png')
    with tempfile.TemporaryDirectory(prefix='bpc-v44-video-') as folder:
        folder=Path(folder);frame=0
        for i,still in enumerate(stills):
            copies=48 if i in (0,len(stills)-1) else 14
            for _ in range(copies):still.save(folder/f'{frame:05d}.png');frame+=1
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(folder/'%05d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'bpc_v44_cross_domain.mp4')],check=True)
    print(OUT/'poster_v44_compressed.png');print(OUT/'bpc_v44_cross_domain.mp4')


if __name__=='__main__':main()
