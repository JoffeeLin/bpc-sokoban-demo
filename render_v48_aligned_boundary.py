#!/usr/bin/env python3
"""Render ten honest v0.48 frozen one-step decisions with English UI."""
import subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

from bpc_aligned_canvas_v47 import aligned_canvas
from bpc_fourth_factor_v28 import step
from bpc_port_interference_v45 import PortInterferenceMedium
from closure_orbit_v46 import orbit_suite
from experiment_v48_aligned_boundary_dev import old_worlds,rows,train

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v48aligned_boundary';W,H=1280,720
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf';NAMES=('LEFT','RIGHT','UP','DOWN')
def font(n,bold=False):return ImageFont.truetype(BOLD if bold else FONT,n)
def grid(draw,state,x,y,size):
    unit=size/7
    for yy in range(7):
        for xx in range(7):
            value=state[yy*8+xx];box=(int(x+xx*unit),int(y+yy*unit),int(x+(xx+1)*unit-2),int(y+(yy+1)*unit-2));draw.rounded_rectangle(box,3,fill='#26334a' if value&1 else '#101722')
            if value&8:draw.ellipse((box[0]+unit*.35,box[1]+unit*.35,box[0]+unit*.65,box[1]+unit*.65),fill='#f6c85f')
            if value&16:draw.rectangle((box[0]+unit*.28,box[1]+unit*.28,box[0]+unit*.72,box[1]+unit*.72),outline='#a78bfa',width=2)
            if value&32:draw.line((box[0]+4,box[1]+4,box[2]-4,box[3]-4),fill='#38bdf8',width=3)
            if value&4:draw.rounded_rectangle((box[0]+unit*.18,box[1]+unit*.18,box[0]+unit*.82,box[1]+unit*.82),3,fill='#f59e0b')
            if value&2:draw.ellipse((box[0]+unit*.18,box[1]+unit*.18,box[0]+unit*.82,box[1]+unit*.82),fill='#34d399')
def title(outro=False):
    image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image);draw.rounded_rectangle((105,80,1175,640),28,fill='#0d1422',outline='#2b466b',width=3)
    draw.text((W//2,150),'PURE BPC v0.48',anchor='mm',font=font(57,True),fill='#f8fafc');draw.text((W//2,222),'Minimal physical closure boundary',anchor='mm',font=font(31),fill='#93c5fd')
    if outro:draw.text((W//2,350),'Code • preregistration • raw evidence',anchor='mm',font=font(30,True),fill='#34d399');draw.text((W//2,415),'github.com/JoffeeLin/bpc-sokoban-demo',anchor='mm',font=font(26),fill='#bfdbfe')
    else:draw.text((W//2,335),'Fresh-seed frozen reproduction: 512 / 512',anchor='mm',font=font(30,True),fill='#34d399');draw.text((W//2,398),'10 unseen layouts shown next',anchor='mm',font=font(26),fill='#e2e8f0')
    draw.text((W//2,535),'No neural network  •  No reward  •  No planner',anchor='mm',font=font(21,True),fill='#a7f3d0');return image
def frame(world,correct,model,index):
    before=aligned_canvas(world);predictions=model.predict_all(before);values=[predictions[a][-1][0] for a in range(4)];chosen=min(range(4),key=values.__getitem__);after=aligned_canvas(step(world,chosen));image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image)
    draw.text((38,25),'Pure BPC v0.48  •  Frozen Unseen Decisions',font=font(32,True),fill='#f8fafc');draw.text((1030,35),'PASS' if chosen==correct else 'FAIL',font=font(20,True),fill='#34d399' if chosen==correct else '#fb7185')
    draw.rounded_rectangle((28,88,835,620),20,fill='#0d1422',outline='#26364f',width=2);draw.text((70,118),'CURRENT PHYSICAL FIELD',font=font(18,True),fill='#94a3b8');draw.text((455,118),f'AFTER BPC: {NAMES[chosen]}',font=font(18,True),fill='#94a3b8');grid(draw,before,65,158,315);grid(draw,after,450,158,315)
    draw.text((65,500),f'Frozen unseen layout {index+1:02d}/10',font=font(24,True),fill='#e2e8f0');draw.text((65,545),'Yellow mark disappears only for the closing action.',font=font(18),fill='#fcd34d')
    draw.rounded_rectangle((865,88,1250,620),20,fill='#0d1422',outline='#26364f',width=2);draw.text((900,125),'P(boundary remains)',font=font(21,True),fill='#93c5fd')
    for a,(name,value) in enumerate(zip(NAMES,values)):
        y=185+a*78;draw.rounded_rectangle((895,y,1218,y+54),10,fill='#123329' if a==chosen else '#172033');draw.text((915,y+15),name,font=font(18,True),fill='#a7f3d0' if a==chosen else '#cbd5e1');draw.text((1195,y+15),f'{value:.3f}',anchor='ra',font=font(19,True),fill='#34d399' if a==chosen else '#e2e8f0')
    draw.text((900,520),'Lowest probability chosen',font=font(17,True),fill='#34d399');draw.text((900,555),'Evaluation writes: 0',font=font(17),fill='#cbd5e1');draw.text((W//2,680),'One-step external closure only — not recurrent internal state, planning, or AGI',anchor='mm',font=font(18,True),fill='#cbd5e1');return image
def main():
    OUT.mkdir(parents=True,exist_ok=True);old=old_worlds();_,dev,_=orbit_suite(481010,150,old);old|=dev;_,dev_holdout,_=orbit_suite(481110,128,old);old|=dev_holdout;training,train_ids,_=orbit_suite(482010,150,old);holdout,_,_=orbit_suite(482110,128,old|train_ids);model=train(PortInterferenceMedium,rows(training));cases=holdout[:10];stills=[title()]+[frame(world,correct,model,i) for i,(world,correct) in enumerate(cases)]+[title(True)];stills[6].save(OUT/'poster_v48_aligned_boundary.png')
    with tempfile.TemporaryDirectory(prefix='bpc-v48-video-') as folder:
        folder=Path(folder);n=0
        for i,still in enumerate(stills):
            for _ in range(48 if i in (0,len(stills)-1) else 19):still.save(folder/f'{n:05d}.png');n+=1
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(folder/'%05d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'bpc_v48_aligned_boundary.mp4')],check=True)
    print(OUT/'poster_v48_aligned_boundary.png');print(OUT/'bpc_v48_aligned_boundary.mp4')
if __name__=='__main__':main()
