import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {
  Film, ArrowRight, ArrowUpRight, UploadCloud, Plus, Play, Pause, Download,
  ChevronLeft, ChevronRight, Layers, Move, Wind, Clapperboard, Trash2,
  FolderPlus, Settings2, Check, LogOut, LoaderCircle, Sparkles, Camera,
  Images, Clock3, Video, SlidersHorizontal, Leaf, MousePointer2, LockKeyhole,
  Mail, Eye, CirclePlay, ArrowDown, CheckCircle2, ImagePlus
} from 'lucide-react';
import './style.css';

const API = '/api';
const req = async (path, opt={}) => {
  const response = await fetch(API + path, {...opt, credentials: 'same-origin'});
  if (!response.ok) {
    let result = {};
    try { result = await response.json(); } catch {}
    throw Error(result.detail || `HTTP ${response.status}`);
  }
  return response.json();
};
const motionNames = {push_in:'Slow push in',pull_out:'Pull back',pan_left:'Pan left',pan_right:'Pan right',track_up:'Track up',track_down:'Track down',static:'Hold frame'};
const effectNames = {none:'None',leaves:'Falling leaves',particles:'Light particles'};
const transitions = {cut:'Clean cut',dissolve:'Soft dissolve',slide:'Slide across'};
const motionIcon = {push_in:'+',pull_out:'−',pan_left:'←',pan_right:'→',track_up:'↑',track_down:'↓',static:'•'};
const ROOT_IMAGE = '/images/icecream.jpg';
const PARK_IMAGE = '/images/park.jpg';

function Brand({onClick}) {
  return <button className="brand" onClick={onClick} aria-label="StoryFrame home">
    <span className="brand-mark"><span className="brand-mark-inner"/></span>
    <span>story<span className="brand-frame">frame</span><span className="brand-stop">.</span></span>
  </button>;
}
function Eyebrow({children}) { return <span className="eyebrow"><span className="eyebrow-line"/>{children}</span>; }
function ArrowButton({children, onClick, kind='primary', disabled=false, type='button', className=''}) {
  return <button type={type} disabled={disabled} onClick={onClick} className={`btn btn-${kind} ${className}`}>
    {children} <ArrowUpRight size={17} strokeWidth={1.8}/>
  </button>;
}

function useLandingScroll(isActive) {
  const hero = useRef(null);
  const story = useRef(null);
  const [step,setStep] = useState(0);
  useEffect(() => {
    if (!isActive) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;
    let raf = 0, previous = -1;
    const update = () => {
      raf = 0;
      const vh = window.innerHeight;
      const y = window.scrollY;
      if (hero.current) {
        const rect = hero.current.getBoundingClientRect();
        const p = Math.max(0, Math.min(1, -rect.top / Math.max(1, rect.height * .85)));
        hero.current.style.setProperty('--hero-scroll', p.toFixed(3));
        hero.current.style.setProperty('--hero-rotate-y', `${-14 + p*21}deg`);
        hero.current.style.setProperty('--hero-rotate-x', `${7 - p*8}deg`);
        hero.current.style.setProperty('--hero-shift-y', `${-38*p}px`);
        hero.current.style.setProperty('--hero-front-x', `${-25*p}px`);
        hero.current.style.setProperty('--hero-front-y', `${25*p}px`);
        hero.current.style.setProperty('--hero-back-x', `${25*p}px`);
        hero.current.style.setProperty('--hero-back-y', `${-75*p}px`);
        hero.current.style.setProperty('--hero-label-y', `${-28*p}px`);
        hero.current.style.setProperty('--hero-label-x', `${42*p}px`);
      }
      if (story.current) {
        const rect = story.current.getBoundingClientRect();
        const range = Math.max(1,rect.height-vh);
        const p = Math.max(0,Math.min(1,-rect.top/range));
        story.current.style.setProperty('--story-scroll',p.toFixed(3));
        story.current.style.setProperty('--story-back-rot', `${-15 + p*18}deg`);
        story.current.style.setProperty('--story-main-rot', `${7 - p*22}deg`);
        story.current.style.setProperty('--story-back-x', `${-30*p}px`);
        story.current.style.setProperty('--story-back-y', `${-135*p}px`);
        story.current.style.setProperty('--story-front-x', `${75*p}px`);
        story.current.style.setProperty('--story-front-y', `${48*p}px`);
        story.current.style.setProperty('--story-particle-opacity', (p*.85).toFixed(2));
        story.current.style.setProperty('--story-particle-one-y', `${-90*p}px`);
        story.current.style.setProperty('--story-particle-two-y', `${-55*p}px`);
        story.current.style.setProperty('--story-particle-three-x', `${35*p}px`);
        const newStep = p < .33 ? 0 : p < .66 ? 1 : 2;
        if (newStep !== previous) { setStep(newStep); previous = newStep; }
      }
    };
    const onScroll = () => { if (!raf) raf = window.requestAnimationFrame(update); };
    window.addEventListener('scroll',onScroll,{passive:true});
    window.addEventListener('resize',onScroll);
    update();
    return () => {window.removeEventListener('scroll',onScroll);window.removeEventListener('resize',onScroll);window.cancelAnimationFrame(raf);};
  },[isActive]);
  return {hero,story,step};
}
function Landing({navigate, user}) {
  const {hero,story,step} = useLandingScroll(true);
  const howRef = useRef(null);
  const steps = [
    {label:'01 / SOURCE',title:'Start with your pages.',detail:'Bring a folder of illustrations or a ZIP. Your artwork stays exactly yours—no AI redraws, no visual drift.',icon:Images},
    {label:'02 / DIRECTION',title:'Give every scene movement.',detail:'Thoughtful camera paths, soft transitions, and a little atmosphere. Adjust each shot in the timeline.',icon:Camera},
    {label:'03 / DELIVERY',title:'A story ready to watch.',detail:'Render a real MP4 locally, review it in the editor, then download only when it feels right.',icon:Video},
  ];
  return <main className="landing-page">
    <section className="hero" ref={hero}>
      <div className="hero-grain"/>
      <div className="hero-inner wrap">
        <div className="hero-copy">
          <Eyebrow>THE STORYBOOK MOTION STUDIO</Eyebrow>
          <h1>Every picture<br/>has a <em>little</em><br/><span className="hero-indent">more to tell.</span></h1>
          <p className="hero-description">Bring still illustrations to life with gentle camera movement, natural atmosphere, and beautifully considered transitions.</p>
          <div className="hero-actions">
            <ArrowButton onClick={()=>navigate(user?'#/dashboard':'#/login')}>Start a new story</ArrowButton>
            <button className="text-link" onClick={()=>howRef.current?.scrollIntoView({behavior:'smooth'})}>See how it works <ArrowRight size={15}/></button>
          </div>
          <div className="hero-footnote"><span className="tiny-orbit"/> Made for stories, not slideshows. <span className="dot-sep">·</span> No dedicated GPU.</div>
        </div>
        <div className="hero-art" aria-label="Two storybook pages forming a layered 3D composition">
          <div className="art-halo"/>
          <div className="art-disc art-disc-one"/>
          <div className="art-disc art-disc-two"/>
          <div className="hero-art-3d">
            <div className="art-plane art-plane-back"><img src={PARK_IMAGE} alt="An illustrated family of cartoon dogs in the park"/></div>
            <div className="art-plane art-plane-front"><div className="art-image"><img src={ROOT_IMAGE} alt="An illustrated family buying ice cream"/></div><div className="art-frame-bottom"><span>01 / Ice cream afternoon</span><span>00:04</span></div></div>
            <span className="art-float-label label-top">a moment, in motion <span>↗</span></span>
            <span className="art-float-label label-bottom"><span className="label-dot"/> camera: slow push in</span>
          </div>
        </div>
      </div>
      <div className="hero-bottom wrap"><span>ANIMATION, WITH A LIGHT TOUCH.</span><span>SCROLL TO EXPLORE <ArrowDown size={14}/></span></div>
    </section>

    <section className="value-bar" ref={howRef}>
      <div className="wrap value-inner">
        <div><span className="value-index">01</span><span>Made for illustrated stories</span></div>
        <div><span className="value-index">02</span><span>Simple, expressive movement</span></div>
        <div><span className="value-index">03</span><span>Rendered on your computer</span></div>
      </div>
    </section>

    <section className="how-intro wrap">
      <div><Eyebrow>FROM STILL TO STORY</Eyebrow><h2>Small movements.<br/><em>Wonderful</em> difference.</h2></div>
      <p>It doesn't take a complicated animation pipeline to make a moment feel alive. StoryFrame keeps the creative process simple—and lets the artwork lead.</p>
    </section>

    <section className="scroll-story" ref={story} aria-label="Explore the StoryFrame animation process">
      <div className="scroll-sticky wrap">
        <div className="scroll-story-content">
          <div className="chapter-count">HOW IT WORKS <span>0{step+1} <span className="thin-slash">/</span> 03</span></div>
          <div className="steps-copy">
            {steps.map((s,i)=><div key={s.title} className={`scroll-step ${step===i?'current':''}`}>
              <span className="step-code">{s.label}</span><h3>{s.title}</h3><p>{s.detail}</p>
            </div>)}
          </div>
          <div className="step-progress">{steps.map((_,i)=><span key={i} className={step===i?'active':''}/>)}</div>
        </div>
        <div className={`scroll-visual step-${step}`}>
          <div className="scroll-grid"/>
          <div className="scroll-orbit"/>
          <div className="scene-plane scene-back"><img src={PARK_IMAGE} alt="A second illustrated story page"/></div>
          <div className="scene-plane scene-main"><img src={ROOT_IMAGE} alt="Cartoon story page with simulated camera depth"/></div>
          <div className="scene-plane scene-overlay"><div className="effect-point effect-one"/><div className="effect-point effect-two"/><div className="effect-point effect-three"/></div>
          <div className="scene-tag scene-tag-a"><span className="tag-pip"/> StoryFrame / 02</div>
          <div className="scene-tag scene-tag-b">{step===0?'Original artwork':step===1?'Camera & atmosphere':'Ready for your audience'}</div>
        </div>
      </div>
    </section>

    <section className="features-section wrap" id="features">
      <div className="feature-heading"><div><Eyebrow>A THOUGHTFUL TOOLKIT</Eyebrow><h2>Just what your<br/>story <em>needs.</em></h2></div><p>Three focused ingredients. One seamless creative process.</p></div>
      <div className="features-grid">
        <article className="feature-card"><div className="feature-number">01 / MOVEMENT</div><div className="feature-illustration camera-illustration"><div className="camera-frame frame-out"/><div className="camera-frame frame-in"/><span className="movement-arrow">↗</span></div><h3>Camera, with intention.</h3><p>Pan, push in, pull back, or track across a page to guide attention naturally.</p></article>
        <article className="feature-card"><div className="feature-number">02 / FLOW</div><div className="feature-illustration flow-illustration"><div className="flow-card flow-a"/><div className="flow-card flow-b"/><span className="flow-spark">✳</span></div><h3>Transitions that breathe.</h3><p>Move from one illustration to the next with cuts, dissolves, or gentle slides.</p></article>
        <article className="feature-card"><div className="feature-number">03 / ATMOSPHERE</div><div className="feature-illustration leaves-illustration"><span>✳</span><span>✦</span><span>✳</span><span>✦</span><span>✳</span></div><h3>A touch of magic.</h3><p>Introduce falling leaves or light particles, without changing your original art.</p></article>
      </div>
    </section>

    <section className="bottom-cta"><div className="wrap bottom-cta-inner"><div><Eyebrow>YOUR NEXT CHAPTER</Eyebrow><h2>A beautiful story<br/>is already <em>there.</em></h2><p>All it needs is a little movement.</p><ArrowButton kind="light" onClick={()=>navigate(user?'#/dashboard':'#/login')}>Open your studio</ArrowButton></div><div className="cta-ornament" aria-hidden="true"><div className="ring ring-one"/><div className="ring ring-two"/><div className="ring ring-three"/><div className="ring-center"><span>sf.</span></div></div></div></section>
    <footer className="footer wrap"><Brand onClick={()=>window.scrollTo({top:0,behavior:'smooth'})}/><span>Made to bring illustrated stories to life.</span><span>StoryFrame © 2026</span></footer>
  </main>;
}

function AuthScreen({authMode,setAuthMode,authenticate,authBusy,navigate,setError}) {
  return <main className="auth-layout">
    <div className="auth-editorial"><div className="auth-editorial-inner"><Eyebrow>YOUR CREATIVE SPACE</Eyebrow><h2>Good stories<br/>deserve a <em>little</em><br/>movement.</h2><p>A calm home for the illustrated worlds you're bringing to life.</p></div><div className="auth-art-pair"><img src={ROOT_IMAGE} alt="Storybook illustration of a family by an ice cream truck"/><img src={PARK_IMAGE} alt="Storybook illustration of the family in a park"/></div><span className="auth-side-note">FROM A SINGLE PAGE TO A MOVING STORY.</span></div>
    <div className="auth-form-side"><div className="auth-card"><Eyebrow>WELCOME TO STORYFRAME</Eyebrow><h1>{authMode==='login'?'Welcome back.':'Start your story.'}</h1><p className="auth-description">{authMode==='login'?'Pick up where your last story left off.':'Create a free account and give your pages a little life.'}</p>
      <div className="auth-tabs" role="tablist" aria-label="Choose sign in or account creation"><button role="tab" aria-selected={authMode==='login'} className={authMode==='login'?'selected':''} onClick={()=>{setAuthMode('login');setError('')}}>Sign in</button><button role="tab" aria-selected={authMode==='register'} className={authMode==='register'?'selected':''} onClick={()=>{setAuthMode('register');setError('')}}>Create account</button></div>
      <form className="auth-form" onSubmit={authenticate}>
        {authMode==='register'&&<div className="field"><label htmlFor="name">Full name</label><input id="name" name="name" placeholder="Your name" autoComplete="name" required maxLength="80"/></div>}
        <div className="field"><label htmlFor="email">Email address</label><input id="email" type="email" name="email" placeholder="name@example.com" required autoComplete="email"/></div>
        <div className="field"><label htmlFor="password">Password</label><input id="password" type="password" name="password" placeholder={authMode==='register'?'At least 8 characters':'Enter your password'} required minLength="8" autoComplete={authMode==='register'?'new-password':'current-password'}/></div>
        <button className="btn btn-primary auth-submit" disabled={authBusy} type="submit">{authBusy?<><LoaderCircle className="spin" size={17}/> Please wait</>:<>{authMode==='login'?'Sign in to your studio':'Create your account'} <ArrowRight size={17}/></>}</button>
      </form>
      <p className="auth-privacy"><LockKeyhole size={14}/> Your stories stay private to your account on this installation.</p>
      <button className="auth-back" onClick={()=>navigate('#/')}><ChevronLeft size={15}/> Back to StoryFrame</button>
    </div></div>
  </main>;
}

function Dashboard({user,projects,uploadName,setUploadName,uploadFiles,setUploadFiles,upload,loading,makeDemo,remove,navigate,inputRef,folderRef}) {
  const fileInput = useRef(null);
  return <main className="dashboard wrap">
    <div className="dashboard-heading"><div><Eyebrow>YOUR CREATIVE WORKSPACE</Eyebrow><h1>Your stories<span className="heading-period">.</span></h1><p>A collection of moments, ready to move.</p></div><button className="btn btn-primary" onClick={()=>inputRef.current?.scrollIntoView({behavior:'smooth',block:'center'})}><Plus size={17}/> New story <ArrowUpRight size={16}/></button></div>
    <div className="dashboard-section-label"><span>YOUR LIBRARY <span className="count">{String(projects.length).padStart(2,'0')}</span></span><span>STORYBOOK PROJECTS</span></div>
    <section className="project-grid">
      {projects.map((p,i)=><article key={p.id} className="project-card"><button className="project-cover" onClick={()=>navigate('#/editor/'+p.id)} aria-label={`Open ${p.name}`}>
        {p.scenes?.[0]&&<img loading="lazy" src={p.scenes[0].imageUrl} alt="Project cover"/>}
        <span className="project-cover-button"><ArrowUpRight size={22}/></span><span className="project-cover-index">PROJECT {String(i+1).padStart(2,'0')}</span>
      </button><div className="project-info"><div><h3>{p.name}</h3><small>{p.scenes.length} scenes <span>·</span> {p.totalDuration}s <span>·</span> {p.videoReady?'Rendered':'In progress'}</small></div><button title="Delete project" aria-label={`Delete ${p.name}`} className="delete-button" onClick={()=>remove(p.id)}><Trash2 size={17}/></button></div></article>)}
      {!projects.length&&<div className="empty-library"><div className="empty-illustration"><Images size={32} strokeWidth={1.4}/></div><h3>A blank page is a good start.</h3><p>Your story projects will live here. Try the sample or bring your own artwork.</p></div>}
    </section>
    <section className="create-section" ref={inputRef} id="new-project"><div className="create-heading"><Eyebrow>BEGIN SOMETHING NEW</Eyebrow><h2>Bring your pages.<br/><em>We'll add the movement.</em></h2><p>Upload a folder of numbered illustrations or a ZIP file. StoryFrame arranges them into scenes in filename order.</p><div className="create-detail"><span><Check size={15}/> JPG, PNG & WEBP</span><span><Check size={15}/> Entire folders & ZIP files</span></div></div>
      <div className="create-form"><label className="field-label" htmlFor="project-name">Project name</label><input id="project-name" className="create-name-input" value={uploadName} onChange={e=>setUploadName(e.target.value)} placeholder="A sunny afternoon"/>
      <input className="hidden-input" ref={fileInput} id="asset-files" type="file" multiple accept=".jpg,.jpeg,.png,.webp,.zip" onChange={e=>setUploadFiles(e.target.files)}/>
      <input className="hidden-input" ref={folderRef} type="file" webkitdirectory="" directory="" multiple onChange={e=>setUploadFiles(e.target.files)}/>
      <button className="upload-dropzone" onClick={()=>fileInput.current?.click()}><span className="upload-icon"><UploadCloud size={25} strokeWidth={1.5}/></span><strong>{uploadFiles?.length?`${uploadFiles.length} file${uploadFiles.length===1?'':'s'} selected`:'Choose your illustrated pages'}</strong><span>{uploadFiles?.length?'Click to change selection':'Select images or one ZIP archive'}</span></button>
      <div className="create-actions"><button className="btn btn-primary" disabled={loading} onClick={upload}>{loading?<LoaderCircle size={16} className="spin"/>:<ImagePlus size={17}/>} Create project <ArrowRight size={16}/></button><button className="btn btn-outline" disabled={loading} onClick={()=>folderRef.current?.click()}><FolderPlus size={16}/> Choose folder</button></div>
      <div className="sample-action"><span>Just exploring?</span><button disabled={loading} onClick={makeDemo}>Open the sample story <ArrowRight size={14}/></button></div>
      </div></section>
  </main>;
}

function Editor({project,selected,setSelected,patch,render,rendering,engine,setEngine,health,watchVideo,setWatchVideo,playing,setPlaying,navigate,load,s,scenes,videoRevision}) {
  const pid = project?.id;
  const isVideo = watchVideo && project?.videoReady;
  const [localTime,setLocalTime] = useState('');
  useEffect(()=>setLocalTime(s?.duration??''),[s?.id,s?.duration]);
  return <main className="editor">
    <div className="editor-toolbar"><button className="editor-back" onClick={()=>{setPlaying(false);navigate('#/dashboard');load()}}><ChevronLeft size={17}/> Library</button><span className="toolbar-divider"/><div className="editor-project-name"><strong>{project?.name || 'Loading story...'}</strong><span>{scenes.length} scenes <span>·</span> {project?.totalDuration||0}s total</span></div><div className="toolbar-spacer"/><div className={`editor-status ${project?.status==='rendering'?'rendering':''}`}><span className="status-dot"/>{project?.status==='rendering'?'Rendering':project?.status==='error'?'Render failed':project?.videoReady?'Video ready':'Draft'}</div><button className="btn btn-primary editor-render" disabled={rendering||project?.status==='rendering'||!scenes.length} onClick={render}>{rendering||project?.status==='rendering'?<LoaderCircle size={16} className="spin"/>:<Clapperboard size={17}/>} {project?.status==='rendering'?'Rendering…':'Render video'}</button></div>
    {project?.error&&<div className="editor-error">{project.error}</div>}
    <div className="editor-layout">
      <div className="editor-stage"><div className="stage-heading"><div><Eyebrow>{isVideo?'FINAL PREVIEW':'STORY CANVAS'}</Eyebrow><h2>{isVideo?'Your story, in motion.':'The scene, as you see it.'}</h2></div><span className="stage-resolution">16:9 <span>·</span> 720p export</span></div>
        <div className="stage-canvas"><div className="stage-center"><div className="preview-screen">
          {isVideo ? <video key={`${pid}-${videoRevision}`} className="final-preview" src={`/api/projects/${pid}/video?v=${videoRevision}`} controls autoPlay playsInline preload="metadata"/> : s ? <img src={s.imageUrl} alt={`Storyboard scene ${selected+1}`} /> : <div className="blank-preview">No scene selected</div>}
          {!isVideo&&s&&<><div className="preview-indicator">SHOT {String(selected+1).padStart(2,'0')} / {String(scenes.length).padStart(2,'0')}</div>{s.effect!=='none'&&<div className={`sample-dust ${s.effect==='leaves'?'leaf':''}`} aria-hidden="true">✦ &nbsp;&nbsp;✧ &nbsp;&nbsp;✦</div>}</>}
        </div></div></div>
        <div className="preview-controls"><div className="preview-left">{project?.videoReady&&<button className="soft-toggle" onClick={()=>{setPlaying(false);setWatchVideo(x=>!x)}}>{isVideo?<Images size={16}/>:<CirclePlay size={16}/>} {isVideo?'Scene view':'Final video'}</button>}<button className="soft-toggle" onClick={()=>setPlaying(v=>!v)} disabled={!scenes.length}>{playing?<Pause size={15}/>:<Play size={15}/>} {playing?'Pause sequence':'Play sequence'}</button></div><span>{s?`${s.duration}s · ${motionNames[s.motion]}`:'No scenes yet'}</span></div>
        {project?.videoReady?<div className="ready-panel"><div><span className="ready-icon"><Check size={16}/></span><div><strong>Your render is ready to review.</strong><span>Watch the finished video here before saving it.</span></div></div><a className="btn btn-primary" href={`/api/projects/${pid}/video`} download={`${project.name}.mp4`}><Download size={16}/> Download MP4</a></div>:<div className="editor-hint"><Sparkles size={16}/> When rendering finishes, the full video will appear here automatically for your final review.</div>}
      </div>
      <aside className="inspector"><div className="inspector-header"><div><Settings2 size={19}/><strong>Scene settings</strong></div><span className="inspector-badge">{selected+1} / {scenes.length}</span></div>
        <div className="inspector-body"><div className="inspector-section"><label className="field-label" htmlFor="engine">RENDER ENGINE</label><select id="engine" value={engine} onChange={e=>setEngine(e.target.value)}><option value="auto">Automatic (recommended)</option><option value="native">Built-in renderer</option><option value="img2vid" disabled={!health?.img2vidAvailable}>img2vid (installed)</option></select><p className="field-caption">{health?.img2vidAvailable?'img2vid found on this computer.':'Auto uses the built-in renderer when img2vid is unavailable.'}</p></div>
        {s?<><div className="inspector-section"><div className="shot-summary"><span>SHOT {String(selected+1).padStart(2,'0')}</span><strong title={s.filename}>{s.filename}</strong></div></div>
          <div className="inspector-section"><label className="field-label" htmlFor="motion">CAMERA DIRECTION</label><select id="motion" value={s.motion} onChange={e=>patch('motion',e.target.value)}>{Object.entries(motionNames).map(([k,v])=><option value={k} key={k}>{v}</option>)}</select></div>
          <div className="inspector-section"><label className="field-label" htmlFor="effect">ATMOSPHERE</label><select id="effect" value={s.effect} onChange={e=>patch('effect',e.target.value)}>{Object.entries(effectNames).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></div>
          <div className="inspector-section"><label className="field-label" htmlFor="transition">TRANSITION</label><select id="transition" value={s.transition} onChange={e=>patch('transition',e.target.value)}>{Object.entries(transitions).map(([k,v])=><option value={k} key={k}>{v}</option>)}</select></div>
          <div className="inspector-section"><label className="field-label" htmlFor="duration">SCENE LENGTH <span>(seconds)</span></label><input id="duration" type="number" min="1" max="30" step="0.5" value={localTime} onChange={e=>setLocalTime(e.target.value)} onBlur={()=>{const val=Number(localTime); if(val>=1&&val<=30&&val!==s.duration)patch('duration',val);else setLocalTime(s.duration);}} onKeyDown={e=>{if(e.key==='Enter')e.currentTarget.blur()}}/></div>
          <div className="inspector-section"><label className="field-label" htmlFor="caption">STORY NOTES <span>(optional)</span></label><textarea id="caption" rows={4} key={`caption-${s.id}`} defaultValue={s.caption||''} onBlur={e=>{if(e.target.value!==s.caption)patch('caption',e.target.value)}} placeholder="A note about this moment…"/></div>
          <div className="inspector-note"><Leaf size={17}/><p>Subtle movements work best. Your original artwork always stays intact.</p></div>
        </>:<div className="inspector-section"><p>No scene selected yet.</p></div>}</div>
      </aside>
    </div>
    <section className="timeline"><div className="timeline-head"><div><Layers size={17}/><strong>Story timeline</strong><span className="timeline-subtitle">One scene at a time, just as your story unfolds.</span></div><span>{project?.totalDuration||0}s <Clock3 size={15}/></span></div>
      <div className="track" role="group" aria-label="Choose a scene to edit">{scenes.map((item,i)=><button key={item.id} className={`clip ${selected===i?'active':''}`} style={{flexGrow:Math.max(1,item.duration)}} onClick={()=>{setPlaying(false);setWatchVideo(false);setSelected(i)}} aria-pressed={selected===i}><img src={item.imageUrl} alt=""/><span className="clip-index">{String(i+1).padStart(2,'0')}</span><span className="clip-footer"><b>Scene {i+1}</b><small>{item.duration}s</small></span></button>)}</div>
      <div className="timeline-ruler"><span>00:00</span><span>{project?.totalDuration||0}s total</span></div>
    </section>
  </main>;
}

function App() {
  const [user,setUser] = useState(null);
  const [authLoading,setAuthLoading] = useState(true);
  const [authMode,setAuthMode] = useState('login');
  const [authBusy,setAuthBusy] = useState(false);
  const [route,setRoute] = useState(window.location.hash || '#/');
  const [projects,setProjects] = useState([]);
  const [project,setProject] = useState(null);
  const [loading,setLoading] = useState(false);
  const [error,setError] = useState('');
  const [selected,setSelected] = useState(0);
  const [playing,setPlaying] = useState(false);
  const [health,setHealth] = useState(null);
  const [engine,setEngine] = useState('auto');
  const [watchVideo,setWatchVideo] = useState(false);
  const [uploadName,setUploadName] = useState('My Story');
  const [uploadFiles,setUploadFiles] = useState(null);
  const [rendering,setRendering] = useState(false);
  const [videoRevision,setVideoRevision] = useState(0);
  const inputRef = useRef(null);
  const folderRef = useRef(null);
  const prevVideoReady = useRef(false);
  const navigate = h=>{window.location.hash=h;setRoute(h);setError('');window.scrollTo(0,0);};
  useEffect(()=>{const onHash=()=>{setRoute(window.location.hash||'#/');setError('');window.scrollTo(0,0)};window.addEventListener('hashchange',onHash);return()=>window.removeEventListener('hashchange',onHash)},[]);
  useEffect(()=>{req('/auth/me').then(setUser).catch(()=>setUser(null)).finally(()=>setAuthLoading(false));req('/health').then(setHealth).catch(()=>{});},[]);
  useEffect(()=>{if(!user&&!authLoading&&(route.startsWith('#/dashboard')||route.startsWith('#/editor/')))navigate('#/login')},[user,authLoading,route]);
  const signOut=async()=>{try{await req('/auth/logout',{method:'POST'})}catch{}setUser(null);setProjects([]);setProject(null);navigate('#/login')};
  const authenticated=info=>{setUser(info);setError('');navigate('#/dashboard')};
  async function authenticate(e){e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));setAuthBusy(true);setError('');try{authenticated(await req('/auth/'+(authMode==='register'?'register':'login'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}))}catch(e){setError(e.message)}finally{setAuthBusy(false)}}
  const load=async()=>{if(!user)return;try{setProjects(await req('/projects'))}catch(e){setError(e.message)}};
  useEffect(()=>{if(user)load()},[user]);
  const pid = route.match(/^#\/editor\/([a-f0-9]+)$/)?.[1];
  const loadProject=async id=>{try{const p=await req(`/projects/${id}`);setProject(p);return p}catch(e){setError(e.message);return null}};
  useEffect(()=>{if(pid&&user){setSelected(0);setPlaying(false);setProject(null);setWatchVideo(false);prevVideoReady.current=false;loadProject(pid)}},[pid,user]);
  useEffect(()=>{if(!pid||!project||project.status!=='rendering')return;const id=setInterval(()=>loadProject(pid),1500);return()=>clearInterval(id)},[pid,project?.status,user]);
  useEffect(()=>{if(!project||project.id!==pid)return;if(project.videoReady&&!prevVideoReady.current){setWatchVideo(true);setPlaying(false);setVideoRevision(n=>n+1)}prevVideoReady.current=!!project.videoReady},[project?.videoReady,project?.id,pid]);
  useEffect(()=>{if(!playing||!project?.scenes?.length)return;const id=setTimeout(()=>setSelected(i=>(i+1)%project.scenes.length),Math.max(1000,(project.scenes[selected]?.duration||4)*1000));return()=>clearTimeout(id)},[playing,selected,project?.id]);
  async function upload(){setError('');if(!uploadFiles?.length){setError('Select images or a ZIP first');return}setLoading(true);try{const f=new FormData();f.append('name',uploadName);let endpoint='/projects/upload';if(uploadFiles.length===1&&uploadFiles[0].name.toLowerCase().endsWith('.zip')){f.append('archive',uploadFiles[0]);endpoint='/projects/upload-zip'}else{[...uploadFiles].forEach(file=>f.append('files',file))}const p=await req(endpoint,{method:'POST',body:f});await load();navigate('#/editor/'+p.id)}catch(e){setError(e.message)}finally{setLoading(false)}}
  async function makeDemo(){setLoading(true);setError('');try{const p=await req('/demo',{method:'POST'});await load();navigate('#/editor/'+p.id)}catch(e){setError(e.message)}finally{setLoading(false)}}
  async function patch(k,v){if(!project?.scenes?.[selected])return;setError('');try{const updated=await req(`/projects/${project.id}/scenes/${project.scenes[selected].id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({[k]:v})});setProject(updated);setWatchVideo(false);prevVideoReady.current=false}catch(e){setError(e.message)}}
  async function render(){if(!project)return;setError('');setRendering(true);setWatchVideo(false);prevVideoReady.current=false;try{await req(`/projects/${project.id}/render?engine=${encodeURIComponent(engine)}`,{method:'POST'});await loadProject(project.id)}catch(e){setError(e.message)}finally{setRendering(false)}}
  async function remove(id){if(!window.confirm('Delete this story?'))return;try{await req(`/projects/${id}`,{method:'DELETE'});await load()}catch(e){setError(e.message)}}
  const landed=route==='#/'||!route;
  const scenes=project?.scenes||[];
  const s=scenes[selected];
  return <>
    <header className={`site-header ${landed?'on-landing':''}`}><div className="header-inner wrap"><Brand onClick={()=>navigate(user?'#/dashboard':'#/')}/>
      <nav className="header-nav" aria-label="Primary navigation">{landed&&<><a href="#features" onClick={e=>{e.preventDefault();document.getElementById('features')?.scrollIntoView({behavior:'smooth'})}}>Features</a><a href="#how-it-works" onClick={e=>{e.preventDefault();document.querySelector('.scroll-story')?.scrollIntoView({behavior:'smooth'})}}>How it works</a></>}{user&&<button onClick={()=>navigate('#/dashboard')}>My studio</button>}</nav>
      <div className="header-actions">{user?<><span className="header-user"><span className="user-avatar">{user.name?.slice(0,1)?.toUpperCase()}</span><span>{user.name}</span></span><button className="header-logout" onClick={signOut} aria-label="Sign out"><LogOut size={16}/> <span>Sign out</span></button></>:<button className="header-cta" onClick={()=>navigate('#/login')}>Enter studio <ArrowUpRight size={16}/></button>}</div>
    </div></header>
    {error&&<div className="global-error" role="alert"><span>{error}</span><button onClick={()=>setError('')} aria-label="Dismiss error">×</button></div>}
    {landed?<Landing navigate={navigate} user={user}/>:route==='#/login'?<AuthScreen authMode={authMode} setAuthMode={setAuthMode} authenticate={authenticate} authBusy={authBusy} navigate={navigate} setError={setError}/>:route==='#/dashboard'?<Dashboard user={user} projects={projects} uploadName={uploadName} setUploadName={setUploadName} uploadFiles={uploadFiles} setUploadFiles={setUploadFiles} upload={upload} loading={loading} makeDemo={makeDemo} remove={remove} navigate={navigate} inputRef={inputRef} folderRef={folderRef}/>:pid?<Editor project={project} selected={selected} setSelected={setSelected} patch={patch} render={render} rendering={rendering} engine={engine} setEngine={setEngine} health={health} watchVideo={watchVideo} setWatchVideo={setWatchVideo} playing={playing} setPlaying={setPlaying} navigate={navigate} load={load} s={s} scenes={scenes} videoRevision={videoRevision}/>:<main className="not-found wrap"><h2>This page is taking a break.</h2><p>Let's get you back to your studio.</p><ArrowButton onClick={()=>navigate(user?'#/dashboard':'#/')}>Go back</ArrowButton></main>}
  </>;
}
createRoot(document.getElementById('root')).render(<App/>);
