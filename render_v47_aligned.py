#!/usr/bin/env python3
"""Render honest frozen v0.47 aligned next-state predictions."""
import random,subprocess,tempfile
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

from bpc_aligned_canvas_v47 import aligned_canvas
from bpc_fourth_factor_v28 import step
from bpc_temporal_cross_generator_v33 import generate
from experiment_v47_aligned_phase1_dev import holdout,old_initials,train,training

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'artifacts'/'v47aligned';W,H=1280,720
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'


def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def hard(prediction):return bytes(sum((p>=.5)<<bit for bit,p in enumerate(cell)) for cell in prediction)


def grid(draw,state,x,y,size,previous=None):
    unit=size/7
    for yy in range(7):
        for xx in range(7):
            index=yy*8+xx;value=state[index];box=(int(x+xx*unit),int(y+yy*unit),int(x+(xx+1)*unit-2),int(y+(yy+1)*unit-2))
            draw.rounded_rectangle(box,3,fill='#26334a' if value&1 else '#101722')
            if value&8:draw.ellipse((box[0]+unit*.36,box[1]+unit*.36,box[0]+unit*.64,box[1]+unit*.64),fill='#f6c85f')
            if value&16:draw.rectangle((box[0]+unit*.28,box[1]+unit*.28,box[0]+unit*.72,box[1]+unit*.72),outline='#a78bfa',width=2)
            if value&32:draw.line((box[0]+4,box[1]+4,box[2]-4,box[3]-4),fill='#38bdf8',width=3)
            if value&4:draw.rounded_rectangle((box[0]+unit*.18,box[1]+unit*.18,box[0]+unit*.82,box[1]+unit*.82),3,fill='#f59e0b')
            if value&2:draw.ellipse((box[0]+unit*.18,box[1]+unit*.18,box[0]+unit*.82,box[1]+unit*.82),fill='#34d399')
            if previous is not None and value!=previous[index]:draw.rounded_rectangle(box,3,outline='#fb7185',width=3)


def frame(row,index):
    current,predicted,actual,action=row;image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image)
    draw.text((38,25),'Pure BPC v0.47  •  Aligned Physical Prediction',font=font(32,True),fill='#f8fafc');draw.text((1000,35),'FROZEN PASS',font=font(18,True),fill='#34d399')
    draw.rounded_rectangle((28,88,935,620),20,fill='#0d1422',outline='#26364f',width=2)
    for label,x in zip(('CURRENT','BPC NEXT (p >= 0.5)','ACTUAL NEXT'),(55,350,645)):draw.text((x,118),label,font=font(17,True),fill='#94a3b8')
    grid(draw,current,55,158,250);grid(draw,predicted,350,158,250,current);grid(draw,actual,645,158,250,current)
    draw.text((55,445),f'Frozen unseen world  •  Step {index+1:02d}/16  •  Action: {action}',font=font(23,True),fill='#e2e8f0')
    draw.text((55,495),'Red outline = changed cell  •  model reads aligned 8-byte rows',font=font(18),fill='#fda4af')
    draw.text((55,542),'No learning occurs during this playback.',font=font(19,True),fill='#a7f3d0')
    draw.rounded_rectangle((960,88,1250,620),20,fill='#0d1422',outline='#26364f',width=2)
    draw.text((990,122),'FROZEN EVIDENCE',font=font(20,True),fill='#93c5fd')
    lines=(('39.79%','unseen contexts'),('0.0465','changed-bit Brier'),('0.0648','unseen-changed Brier'),('83.52%','better than no-action'),('0','evaluation writes'))
    for i,(value,label) in enumerate(lines):draw.text((990,178+i*78),value,font=font(28,True),fill='#34d399');draw.text((990,211+i*78),label,font=font(15),fill='#cbd5e1')
    draw.text((W//2,676),'World prediction only — not goal solving, planning, cross-domain transfer, or AGI',anchor='mm',font=font(18,True),fill='#cbd5e1')
    return image


def title(outro=False):
    image=Image.new('RGB',(W,H),'#070b12');draw=ImageDraw.Draw(image);draw.rounded_rectangle((110,85,1170,635),28,fill='#0d1422',outline='#2b466b',width=3)
    draw.text((W//2,150),'PURE BPC v0.47',anchor='mm',font=font(56,True),fill='#f8fafc');draw.text((W//2,220),'Aligned one-step physical prediction',anchor='mm',font=font(31),fill='#93c5fd')
    if outro:
        draw.text((W//2,335),'Code • preregistration • raw evidence',anchor='mm',font=font(29,True),fill='#34d399');draw.text((W//2,397),'github.com/JoffeeLin/bpc-sokoban-demo',anchor='mm',font=font(27),fill='#bfdbfe')
    else:
        draw.text((W//2,315),'Fresh-seed frozen reproduction: PASS',anchor='mm',font=font(28,True),fill='#34d399');draw.text((W//2,375),'39.79% unseen contexts  •  zero evaluation writes',anchor='mm',font=font(25),fill='#e2e8f0');draw.text((W//2,435),'Corrects the v0.44 camera-stride defect',anchor='mm',font=font(23),fill='#fda4af')
    draw.text((W//2,535),'No neural network  •  No reward  •  No planner',anchor='mm',font=font(21,True),fill='#a7f3d0');return image


def trace():
    old=old_initials();_,dev,_,_,_=training(247010,old);_,suite,_=holdout(247110,old|dev);old|=dev|{(w.h,w.w,w.walls,w.agent,w.objects,w.marks,w.switches,w.gates) for _,w,_ in suite}
    rows,initials,_,_,_=training(247210,old);medium=train(rows);demo,_=generate(247410,1,old|initials);world=demo[0][1];rng=random.Random(247411);names=('LEFT','RIGHT','UP','DOWN');out=[]
    for _ in range(16):
        action=rng.randrange(4);before=aligned_canvas(world);world=step(world,action);actual=aligned_canvas(world);out.append((before,hard(medium.predict(before,action)),actual,names[action]))
    return out


def main():
    OUT.mkdir(parents=True,exist_ok=True);rows=trace();stills=[title()]+[frame(row,i) for i,row in enumerate(rows)]+[title(True)];stills[8].save(OUT/'poster_v47_aligned.png')
    with tempfile.TemporaryDirectory(prefix='bpc-v47-video-') as folder:
        folder=Path(folder);n=0
        for i,still in enumerate(stills):
            for _ in range(48 if i in (0,len(stills)-1) else 12):still.save(folder/f'{n:05d}.png');n+=1
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(folder/'%05d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'bpc_v47_aligned_prediction.mp4')],check=True)
    print(OUT/'poster_v47_aligned.png');print(OUT/'bpc_v47_aligned_prediction.mp4')


if __name__=='__main__':main()
