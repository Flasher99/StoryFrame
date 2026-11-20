"""Deterministic particles/leaves composition over externally generated MP4."""
from __future__ import annotations
import math
import subprocess
from pathlib import Path
import cv2
import numpy as np


def effect_for_time(scenes, seconds):
    elapsed=0.0
    for s in scenes:
        elapsed+=float(s['duration'])
        if seconds<elapsed:
            return s['effect'],s['id'],(seconds-(elapsed-float(s['duration'])))/max(float(s['duration']),.01)
    s=scenes[-1]
    return s['effect'],s['id'],1.0


def compose_effects(base_video: Path, final_video: Path, scenes: list[dict], fps=24):
    if not any(s['effect'] != 'none' for s in scenes):
        base_video.replace(final_video)
        return
    cap=cv2.VideoCapture(str(base_video))
    if not cap.isOpened(): raise RuntimeError('Cannot decode img2vid output')
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps=cap.get(cv2.CAP_PROP_FPS) or fps
    cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{w}x{h}',
         '-r',str(actual_fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast',
         '-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(final_video)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        idx=0
        while True:
            ok,frame=cap.read()
            if not ok:break
            eff,sid,_=effect_for_time(scenes,idx/actual_fps)
            if eff!='none':
                overlay=frame.copy();seed=int(sid[:8],16)
                for j in range(22 if eff=='particles' else 14):
                    phase=(j*.6180339887+seed*.000001)%1
                    x=int(((phase+ .055*math.sin(idx/actual_fps+j*.23))%1)*w)
                    y=int((((j*.137+seed*.00000003+(idx/actual_fps)*(.13 if eff=='leaves' else -.045))%1))*h)
                    if eff=='leaves':
                        pts=np.array([[x,y-5],[x+5,y],[x,y+5],[x-3,y]],dtype=np.int32)
                        cv2.fillConvexPoly(overlay,pts,(62+j%3*17,130+j%3*15,170+j%2*20))
                    else:
                        cv2.circle(overlay,(x,y),1+j%3,(226,233,250),-1,cv2.LINE_AA)
                cv2.addWeighted(overlay,.28,frame,.72,0,frame)
            proc.stdin.write(frame.tobytes());idx+=1
    finally:
        cap.release()
        if proc.stdin:proc.stdin.close()
    err=proc.stderr.read().decode(errors='replace')
    rc=proc.wait()
    proc.stderr.close()
    if rc: raise RuntimeError('Effects encoding failed: '+err[-1000:])
    base_video.unlink(missing_ok=True)
