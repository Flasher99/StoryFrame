"""Optional real img2vid CLI adapter.

Uses installed upstream executable; does NOT vendor upstream source code.
StoryFrame owns the UI, projects, scene settings and atmospheric compositing.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
from pathlib import Path


def discover_img2vid() -> str | None:
    override = os.environ.get('IMG2VID_BIN')
    if override:
        p=Path(override).expanduser()
        return str(p) if p.is_file() and os.access(p,os.X_OK) else None
    found=shutil.which('img2vid')
    if found: return found
    for path in [Path.home()/'Downloads'/'img2vid'/'.venv'/'bin'/'img2vid',
                 Path.home()/'img2vid'/'.venv'/'bin'/'img2vid']:
        if path.is_file() and os.access(path,os.X_OK): return str(path)
    return None


def build_storyboard(scenes: list[dict], image_dir: Path, fps: int=24) -> dict:
    """Translate editable StoryFrame scenes to the upstream storyboard schema.

    Upstream defines transition as outgoing on each scene, while the StoryFrame
    editor defines it as incoming on the next scene.
    """
    motion_map={'push_in':('zoom_in',1.15), 'pull_out':('zoom_out',1.15),
                'pan_left':('pan',1.10), 'pan_right':('pan',1.10),
                'track_up':('pan',1.12), 'track_down':('pan',1.12),
                'static':('zoom_in',1.005)}
    focus_map={'pan_left':[0.15,0.5],'pan_right':[0.85,0.5],
               'track_up':[0.5,0.15],'track_down':[0.5,0.85]}
    transitions={'dissolve':'crossfade','slide':'slide','cut':'cut'}
    result=[]
    for idx, scene in enumerate(scenes):
        motion,zoom=motion_map.get(scene['motion'],motion_map['static'])
        outgoing = scenes[idx+1]['transition'] if idx+1<len(scenes) else 'cut'
        result.append({
            'image':str((image_dir/scene['filename']).resolve()),
            'duration':float(scene['duration']),
            'motion':motion,'zoom':zoom,'focus':focus_map.get(scene['motion'],[0.5,0.5]),
            'fit':'contain' if scene['motion']=='static' else 'cover',
            'transition':transitions.get(outgoing,'cut'),
            'caption':scene.get('caption') or '', 'depth':False,
            'animate':False
        })
    return {'aspect':'16:9','fps':fps,'music':None,'title':'','transition_duration':0.45,
            'fade_in':0.0,'fade_out':0.0,'scenes':result}


def run_img2vid(executable: str, scenes: list[dict], image_dir: Path,
                video_path: Path, fps: int=24, resolution: int=540) -> Path:
    storyboard=build_storyboard(scenes,image_dir,fps)
    json_path=video_path.with_suffix('.storyboard.json')
    json_path.write_text(json.dumps(storyboard,indent=2),encoding='utf-8')
    cmd=[executable,'render',str(json_path),'-o',str(video_path),'--resolution',str(resolution)]
    try:
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=60*45,check=False)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError('img2vid timed out after 45 minutes') from e
    if cp.returncode!=0:
        raise RuntimeError('img2vid failed: '+(cp.stderr or cp.stdout)[-1000:])
    if not video_path.exists() or video_path.stat().st_size < 100:
        raise RuntimeError('img2vid did not create a playable output file')
    return video_path
