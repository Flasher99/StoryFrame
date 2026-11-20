import io, os, tempfile, time, unittest
from pathlib import Path
from PIL import Image

# Must set DATA before importing app
_tmp=tempfile.TemporaryDirectory()
os.environ['STORYFRAME_DATA']=_tmp.name
from fastapi.testclient import TestClient
from backend.app import app, render_scene
import cv2
import numpy as np
client=TestClient(app)
res=client.post('/api/auth/register',json={'name':'Tester','email':'tester-'+__import__('uuid').uuid4().hex+'@example.com','password':'strongpass123'})
assert res.status_code == 200, res.text


def pic(color):
    buf=io.BytesIO();Image.new('RGB',(320,180),color).save(buf,format='JPEG');return buf.getvalue()

class StoryFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        resp=client.post('/api/projects/upload',data={'name':'test',},files=[('files',('page10.jpg',pic('red'),'image/jpeg')),('files',('page2.jpg',pic('blue'),'image/jpeg'))]);assert resp.status_code==200,resp.text
        cls.p=resp.json();cls.pid=cls.p['id']
    def test_01_upload_and_order(self):
        self.assertEqual(len(self.p['scenes']),2)
        self.assertEqual(self.p['scenes'][0]['order'],0) # first sorted scene has index 0
        from PIL import Image
        import io
        data=client.get(f'/api/projects/{self.pid}/scenes/{self.p["scenes"][0]["id"]}/image').content
        r,g,b=Image.open(io.BytesIO(data)).convert('RGB').getpixel((10,10))
        self.assertGreater(b,r) # page2 (blue) is ordered before page10
        self.assertEqual(client.get(f'/api/projects/{self.pid}').status_code,200)
        self.assertEqual(TestClient(app).get(f'/api/projects/{self.pid}').status_code,401)
    def test_02_edit(self):
        sid=self.p['scenes'][0]['id']
        resp=client.patch(f'/api/projects/{self.pid}/scenes/{sid}',json={'duration':1,'effect':'particles','motion':'pan_left'})
        self.assertEqual(resp.status_code,200,resp.text)
        self.assertEqual(resp.json()['scenes'][0]['duration'],1)
        self.assertEqual(client.patch(f'/api/projects/{self.pid}/scenes/{sid}',json={'motion':'bad'}).status_code,400)
    def test_03_image_access(self):
        sid=self.p['scenes'][0]['id']
        self.assertEqual(client.get(f'/api/projects/{self.pid}/scenes/{sid}/image').status_code,200)
    def test_04_camera_effects(self):
        image=np.full((240,320,3),160,np.uint8)
        scene={'id':'abcdef12','motion':'push_in','effect':'leaves'}
        frame=render_scene(scene,image,.6,320,180)
        self.assertEqual(frame.shape,(180,320,3))
    def test_05_render_mp4(self):
        for s in self.p['scenes']:
            client.patch(f'/api/projects/{self.pid}/scenes/{s["id"]}',json={'duration':1,'transition':'dissolve'})
        resp=client.post(f'/api/projects/{self.pid}/render')
        self.assertEqual(resp.status_code,200,resp.text)
        for _ in range(80):
            p=client.get(f'/api/projects/{self.pid}').json()
            if p['status']!='rendering':break
            time.sleep(.25)
        self.assertEqual(p['status'],'ready',p['error'])
        v=client.get(f'/api/projects/{self.pid}/video')
        self.assertEqual(v.status_code,200)
        self.assertGreater(len(v.content),3000)
    def test_06_zip_upload(self):
        with io.BytesIO() as stream:
            import zipfile
            with zipfile.ZipFile(stream,'w') as z:
                z.writestr('folder/pic1.jpg',pic('green'))
            b=stream.getvalue()
        r=client.post('/api/projects/upload-zip',data={'name':'ZIP',},files={'archive':('sample.zip',b,'application/zip')})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(len(r.json()['scenes']),1)
if __name__=='__main__':unittest.main()

class Img2vidBridgeTests(unittest.TestCase):
    def test_storyboard_mapping(self):
        from backend.img2vid_bridge import build_storyboard
        scenes=[{'id':'abcdef12','filename':'one.jpg','duration':4,'motion':'pan_left','effect':'leaves','transition':'cut','caption':'First'},
                {'id':'abcdef13','filename':'two.jpg','duration':5,'motion':'push_in','effect':'none','transition':'dissolve','caption':''}]
        board=build_storyboard(scenes,Path('/tmp'),24)
        self.assertEqual(board['scenes'][0]['motion'],'pan')
        self.assertEqual(board['scenes'][0]['transition'],'crossfade')
        self.assertEqual(board['scenes'][1]['transition'],'cut')
        self.assertFalse(board['scenes'][0]['depth'])
        self.assertEqual(board['fps'],24)

    def test_adapter_and_effects_with_mock_renderer(self):
        # Tests our executable integration and MP4 effects overlay, not upstream img2vid itself.
        import subprocess
        from backend.img2vid_bridge import run_img2vid
        from backend.effects import compose_effects
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);image=root/'image.jpg';image.write_bytes(pic('blue'))
            script=root/'mock_img2vid'
            script.write_text('''#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
assert sys.argv[1]=='render'
j=json.loads(Path(sys.argv[2]).read_text())
assert j['scenes'][0]['image']
out=sys.argv[sys.argv.index('-o')+1]
subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-framerate','12','-i',j['scenes'][0]['image'],'-t','1','-vf','scale=320:180','-c:v','libx264','-pix_fmt','yuv420p',out],check=True)
''')
            script.chmod(0o755)
            s=[{'id':'abcd1234','filename':'image.jpg','duration':1,'motion':'push_in','effect':'particles','transition':'cut','caption':''}]
            base=root/'base.mp4';final=root/'final.mp4'
            run_img2vid(str(script),s,root,base,fps=12,resolution=180)
            self.assertTrue(base.is_file())
            compose_effects(base,final,s,fps=12)
            self.assertTrue(final.is_file())
            self.assertGreater(final.stat().st_size,3000)
