"""StoryFrame MVP - local storybook motion comic API.
Run with: uvicorn backend.app:app --reload --port 8000
"""
from __future__ import annotations
import io, json, math, os, re, sqlite3, subprocess, threading, time, uuid, zipfile
from pathlib import Path
from contextlib import contextmanager
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from backend.img2vid_bridge import discover_img2vid, run_img2vid
from backend.effects import compose_effects
from backend.auth import router as auth_router, init_auth, current_owner

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get('STORYFRAME_DATA', str(ROOT / 'data')))
DATA.mkdir(parents=True, exist_ok=True)
DB = DATA / 'storyframe.sqlite'
ALLOWED = {'.png', '.jpg', '.jpeg', '.webp'}
MAX_FILES = 150
MAX_BYTES = 15 * 1024 * 1024
app = FastAPI(title='StoryFrame Motion Comic API', version='1.1')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://storyframe-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@contextmanager
def conn():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.execute('CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, owner TEXT NOT NULL, created_at REAL NOT NULL, status TEXT DEFAULT "ready", error TEXT, video TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS scenes (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, ord INTEGER NOT NULL, filename TEXT NOT NULL, duration REAL NOT NULL, motion TEXT NOT NULL, effect TEXT NOT NULL, transition TEXT NOT NULL, caption TEXT DEFAULT "", FOREIGN KEY(project_id) REFERENCES projects(id))')
        c.commit()
init_db()
init_auth(DB)
app.include_router(auth_router)


def safe_owner(owner: str) -> str:
    return (owner or 'demo').strip().lower()[:80]


def project_info(pid: str, owner='demo') -> dict:
    with conn() as c:
        p = c.execute('SELECT * FROM projects WHERE id=? AND owner=?', (pid, safe_owner(owner))).fetchone()
        if not p: raise HTTPException(404, 'Project not found')
        s = c.execute('SELECT * FROM scenes WHERE project_id=? ORDER BY ord', (pid,)).fetchall()
    return {'id': p['id'], 'name': p['name'], 'owner': p['owner'], 'status': p['status'], 'error': p['error'], 'videoReady': bool(p['status']=='ready' and p['video'] and Path(p['video']).exists()), 'createdAt': p['created_at'], 'totalDuration': round(sum(row['duration'] for row in s), 2), 'scenes': [{'id':r['id'], 'order':r['ord'], 'filename':r['filename'], 'duration':r['duration'], 'motion':r['motion'], 'effect':r['effect'], 'transition':r['transition'], 'caption':r['caption'], 'imageUrl':f'/api/projects/{pid}/scenes/{r["id"]}/image?owner={safe_owner(owner)}'} for r in s]}


def natural_key(v: str):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)', v)]


def is_image_valid(raw: bytes) -> bool:
    try:
        im = Image.open(io.BytesIO(raw)); im.verify()
        return True
    except Exception: return False


def add_project(name, owner, items):
    if not items: raise HTTPException(400, 'No supported images found')
    if len(items)>MAX_FILES: raise HTTPException(400, f'Maximum {MAX_FILES} images')
    pid = uuid.uuid4().hex
    folder = DATA / 'projects' / pid / 'images'; folder.mkdir(parents=True, exist_ok=True)
    items.sort(key=lambda item: natural_key(item[0]))
    with conn() as c:
        c.execute('INSERT INTO projects (id,name,owner,created_at) VALUES (?,?,?,?)',(pid,name[:100],safe_owner(owner),time.time()))
        for n,(filename,raw) in enumerate(items):
            if len(raw)>MAX_BYTES or not is_image_valid(raw): continue
            sid=uuid.uuid4().hex
            dest=folder/f'{n:04d}_{sid}.jpg'
            with Image.open(io.BytesIO(raw)) as im:
                im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((2400,2400)); im.save(dest,quality=91)
            c.execute('INSERT INTO scenes (id,project_id,ord,filename,duration,motion,effect,transition,caption) VALUES (?,?,?,?,?,?,?,?,?)', (sid,pid,n,dest.name,4.0, ['push_in','pan_right','pan_left','pull_out'][n%4], ['leaves','particles','none'][n%3], 'dissolve' if n else 'cut', ''))
        count=c.execute('SELECT COUNT(*) FROM scenes WHERE project_id=?',(pid,)).fetchone()[0]
        if not count:
            c.rollback()
            raise HTTPException(400,'Images were invalid or too large')
        c.commit()
    return project_info(pid,owner)


@app.get('/api/health')
def health():
    exe=discover_img2vid()
    return {'ok':True,'preferredRenderer':'img2vid' if exe else 'native','img2vidAvailable':bool(exe),
            'img2vidExecutable':exe,'gpuRequired':False,'nativeFallbackAvailable':True}


@app.get('/api/projects')
def projects(owner: str = Depends(current_owner)):
    with conn() as c: rows=c.execute('SELECT id FROM projects WHERE owner=? ORDER BY created_at DESC',(safe_owner(owner),)).fetchall()
    return [project_info(r['id'],owner) for r in rows]


@app.post('/api/projects/upload')
async def upload_project(name: str=Form('My Story'), owner: str=Depends(current_owner), files: list[UploadFile]=File(...)):
    items=[]
    for f in files:
        fname=Path(f.filename or '').name
        if Path(fname).suffix.lower() not in ALLOWED: continue
        raw=await f.read(MAX_BYTES+1)
        items.append((fname,raw))
    return add_project(name,owner,items)


@app.post('/api/projects/upload-zip')
async def upload_zip(name: str=Form('My Story'), owner: str=Depends(current_owner), archive: UploadFile=File(...)):
    data=await archive.read(120*1024*1024+1)
    if len(data)>120*1024*1024: raise HTTPException(413,'ZIP too large')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            members=[x for x in z.infolist() if not x.is_dir() and Path(x.filename).suffix.lower() in ALLOWED and not Path(x.filename).name.startswith('.')]
            if len(members)>MAX_FILES: raise HTTPException(400,'Too many images')
            items=[]
            for m in members:
                if m.file_size>MAX_BYTES: continue
                items.append((Path(m.filename).name,z.read(m)))
    except zipfile.BadZipFile: raise HTTPException(400,'Invalid ZIP archive')
    return add_project(name,owner,items)


@app.get('/api/projects/{pid}')
def get_project(pid: str,owner: str=Depends(current_owner)): return project_info(pid,owner)


@app.get('/api/projects/{pid}/scenes/{sid}/image')
def image_file(pid: str,sid: str,owner: str=Depends(current_owner)):
    project_info(pid,owner)
    with conn() as c: row=c.execute('SELECT filename FROM scenes WHERE id=? AND project_id=?',(sid,pid)).fetchone()
    if not row: raise HTTPException(404,'Image not found')
    path=DATA/'projects'/pid/'images'/row['filename']
    return FileResponse(path,media_type='image/jpeg')


class ScenePatch(BaseModel):
    duration: float|None = Field(default=None,ge=1,le=30)
    motion: str|None = None
    effect: str|None = None
    transition: str|None = None
    caption: str|None = None


@app.patch('/api/projects/{pid}/scenes/{sid}')
def update_scene(pid: str,sid: str,patch: ScenePatch,owner: str=Depends(current_owner)):
    project_info(pid,owner)
    updates=patch.model_dump(exclude_unset=True)
    allowed={'motion': {'push_in','pull_out','pan_left','pan_right','track_up','track_down','static'},'effect':{'none','leaves','particles'},'transition':{'cut','dissolve','slide'}}
    for k,values in allowed.items():
        if k in updates and updates[k] not in values: raise HTTPException(400,f'Invalid {k}')
    if 'caption' in updates and updates['caption'] is not None: updates['caption']=updates['caption'][:250]
    updates={k:v for k,v in updates.items() if v is not None}
    if updates:
        with conn() as c:
            if not c.execute('SELECT 1 FROM scenes WHERE id=? AND project_id=?',(sid,pid)).fetchone(): raise HTTPException(404,'Scene not found')
            c.execute(f'UPDATE scenes SET {", ".join(k+"=?" for k in updates)} WHERE id=? AND project_id=?',(*updates.values(),sid,pid))
            c.execute('UPDATE projects SET video=NULL WHERE id=?',(pid,))
            c.commit()
    return project_info(pid,owner)


@app.delete('/api/projects/{pid}')
def delete_project(pid: str,owner: str=Depends(current_owner)):
    project_info(pid,owner)
    with conn() as c:
        c.execute('DELETE FROM scenes WHERE project_id=?',(pid,))
        c.execute('DELETE FROM projects WHERE id=?',(pid,))
        c.commit()
    import shutil
    shutil.rmtree(DATA/'projects'/pid,ignore_errors=True)
    return {'ok':True}


def eased(t):
    t=np.clip(t,0,1)
    return t*t*(3-2*t)


def render_scene(scene: dict, image: np.ndarray, t: float, width=960, height=540) -> np.ndarray:
    """Single scene camera move, atmospheric effects. No complex rigging."""
    ih,iw=image.shape[:2]; aspect=width/height
    # Fit full frame with border-safe cover crop, then reserve 12% overscan for motion.
    base_scale=max(width/iw,height/ih)
    p=eased(t)
    motion=scene['motion']
    zoom = (1.025+0.125*p) if motion=='push_in' else (1.15-0.125*p) if motion=='pull_out' else 1.09
    scale=base_scale*zoom
    sw,sh=iw*scale,ih*scale
    maxdx=max(0,(sw-width)/2); maxdy=max(0,(sh-height)/2)
    dx=dy=0
    if motion=='pan_right': dx=(-0.86+1.72*p)*maxdx
    if motion=='pan_left': dx=(0.86-1.72*p)*maxdx
    if motion=='track_up': dy=(0.86-1.72*p)*maxdy
    if motion=='track_down': dy=(-0.86+1.72*p)*maxdy
    if motion=='push_in': dx=(p-.5)*maxdx*.4
    mat=np.array([[scale,0,width/2-sw/2-dx],[0,scale,height/2-sh/2-dy]],dtype=np.float32)
    frame=cv2.warpAffine(image,mat,(width,height),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    # Deterministic, inexpensive particles overlaid in image space.
    if scene['effect']!='none':
        overlay=frame.copy(); sid=int(scene['id'][:8],16)
        for j in range(20 if scene['effect']=='particles' else 13):
            phase=(j*0.61803398875+sid*.000001)%1
            x=int(((phase+0.09*math.sin((t+j*.1)*math.pi*2))%1)*width)
            y=int((((j*.137+sid*.00000003+t*(.19 if scene['effect']=='leaves' else -.065))%1))*height)
            if scene['effect']=='leaves':
                pts=np.array([[x,y-4],[x+6,y],[x,y+4],[x-4,y]],np.int32)
                cv2.fillConvexPoly(overlay,pts,(70+(j%3)*20,135+(j%3)*13,193+(j%2)*20))
            else:
                cv2.circle(overlay,(x,y),1+j%3,(235,232,203),-1,cv2.LINE_AA)
        frame=cv2.addWeighted(overlay,.29 if scene['effect']=='leaves' else .35,frame,.71 if scene['effect']=='leaves' else .65,0)
    return frame


def create_video(pid: str,owner: str, width=1280,height=720,fps=24,engine="auto"):
    info=project_info(pid,owner)
    folder=DATA/'projects'/pid
    out=folder/'storyframe.mp4'; tmp=folder/'intermediate.mp4'
    with conn() as c:
        c.execute('UPDATE projects SET status=?,error=NULL,video=NULL WHERE id=?',('rendering',pid));c.commit()
    try:
        if not shutil_which('ffmpeg'): raise RuntimeError('FFmpeg is not installed')
        executable=discover_img2vid()
        if engine=='img2vid' and not executable:
            raise RuntimeError('img2vid not installed. Install it, or select built-in renderer.')
        if engine!='native' and executable:
            external=folder/'img2vid_base.mp4'
            external.unlink(missing_ok=True)
            run_img2vid(executable,info['scenes'],folder/'images',external,fps=24,resolution=720)
            compose_effects(external,out,info['scenes'],fps=24)
            with conn() as c:
                c.execute('UPDATE projects SET status=?,error=NULL,video=? WHERE id=?',('ready',str(out),pid));c.commit()
            return
        raw_scenes=[]
        for scene in info['scenes']:
            path=folder/'images'/scene['filename']
            im=cv2.imread(str(path))
            if im is None: raise RuntimeError(f'Cannot read {scene["filename"]}')
            raw_scenes.append((scene,im))
        cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{width}x{height}','-r',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','ultrafast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(tmp)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            prev=None
            for idx,(scene,im) in enumerate(raw_scenes):
                count=round(scene['duration']*fps)
                trans=min(round(.45*fps),count//3) if idx and scene['transition']!='cut' else 0
                for f in range(count):
                    fr=render_scene(scene,im,f/max(1,count-1),width,height)
                    if trans and f<trans and prev is not None:
                        mix=(f+1)/(trans+1)
                        if scene['transition']=='slide':
                            offset=int(width*mix)
                            nxt=fr.copy(); fr=prev.copy()
                            if offset>0:
                                fr[:,:width-offset]=prev[:,offset:]
                                fr[:,width-offset:]=nxt[:,:offset]
                        else: fr=cv2.addWeighted(prev,1-mix,fr,mix,0)
                    proc.stdin.write(fr.tobytes())
                prev=render_scene(scene,im,1.0,width,height)
        except (BrokenPipeError,OSError):
            raise RuntimeError('FFmpeg encoding failed')
        finally:
            if proc.stdin: proc.stdin.close()
        err=proc.stderr.read().decode('utf-8',errors='replace')
        rc=proc.wait()
        proc.stderr.close()
        if rc: raise RuntimeError(err[-1000:] or f'FFmpeg exited {rc}')
        os.replace(tmp,out)
        with conn() as c:
            c.execute('UPDATE projects SET status=?,error=NULL,video=? WHERE id=?',('ready',str(out),pid));c.commit()
    except Exception as e:
        with conn() as c:
            c.execute('UPDATE projects SET status=?,error=? WHERE id=?',('error',str(e)[:1000],pid));c.commit()


def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)


@app.post('/api/projects/{pid}/render')
def render(pid: str,owner: str=Depends(current_owner), engine: str='auto'):
    if engine not in ('auto','native','img2vid'): raise HTTPException(400,'Invalid renderer')
    p=project_info(pid,owner)
    if p['status']=='rendering': raise HTTPException(409,'Render already in progress')
    with conn() as c:
        c.execute('UPDATE projects SET status=?,error=NULL WHERE id=?',('rendering',pid));c.commit()
    threading.Thread(target=create_video,args=(pid,owner,1280,720,24,engine),daemon=True).start()
    return {'status':'rendering','projectId':pid}


@app.get('/api/projects/{pid}/video')
def video(pid: str,owner: str=Depends(current_owner)):
    p=project_info(pid,owner)
    if not p['videoReady']: raise HTTPException(404,'Video not rendered yet')
    path=DATA/'projects'/pid/'storyframe.mp4'
    return FileResponse(path,media_type='video/mp4',filename=f'{p["name"][:48]}.mp4',content_disposition_type='inline')


@app.post('/api/demo')
def demo(owner: str=Depends(current_owner)):
    assets=ROOT/'assets'
    images=[(p.name,p.read_bytes()) for p in sorted(assets.glob('scene*.jpg'))]
    return add_project('Ice Cream to Park — Demo',owner,images)
