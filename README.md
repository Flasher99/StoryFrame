# StoryFrame — Earthy Studio Edition

StoryFrame is a local-first web application that turns a folder or ZIP archive of illustrated story pages into a cinematic motion-comic MP4, without a generative video model or dedicated GPU.

## What's new in this edition

- Completely redesigned **minimal, editorial, earthy** user interface for all four pages: landing, email/password login, dashboard and timeline editor.
- **3D scroll animation** on the landing page: perspective-tilting storybook panels and a scroll-driven three-stage layered story sequence. Implemented with CSS 3D transforms + `requestAnimationFrame` scroll updates, with a reduced-motion alternative. No WebGL, Three.js, paid effects plugin, or AI/video GPU needed.
- Google sign-in has been **removed from the interface and from the backend authentication endpoints**. Email/password account creation and login remain. The existing SQLite user schema remains backward-compatible; no user records are deleted by upgrading.
- Fixed the broken render request: `/api/projects/{id}/render?engine=auto` (not `/render&engine=auto`).
- The finished MP4 appears automatically **inside the editor for review before download**. Scene edits invalidate the previous video and require another render.
- The original StoryFrame backend, upload pipeline, img2vid adapter, particle/leaves compositor, and native fallback remain in place.

## Requirements

- macOS (including Apple Silicon) or Linux
- Python 3.10 or newer
- Node.js 18 or newer
- FFmpeg (`brew install ffmpeg` on macOS)
- No external API keys, no dedicated GPU

## Start the backend

From the extracted `storyframe_mvp` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

## Start the frontend

Open another terminal:

```bash
cd storyframe_mvp/frontend
npm install
npm run dev
```

Navigate to **http://127.0.0.1:5173**. Choose **Enter studio**, create an account (or sign in with your existing email/password), then create a project or select **Open the sample story**.

## Render a video

1. Upload a folder of JPG/PNG/WEBP pages, select multiple images, or upload a ZIP.
2. Open the resulting project; pages are ordered by filename.
3. Edit camera direction, transition, atmosphere and scene duration in the inspector.
4. Select **Render video**. The backend renders in a thread, and the editor polls the status.
5. When the MP4 is ready, the editor switches to the actual video player. Watch it and select **Download MP4** if you're happy with the result.

Each scene supports camera push/pull/pan/track, transitions (cut/dissolve/slide), and atmosphere (leaves/particles/none).

## Optional img2vid integration

StoryFrame does not bundle third-party img2vid. The editor's **Automatic** engine uses the installed CLI when detected and otherwise uses the bundled native renderer. To point explicitly at a local img2vid executable, before starting the backend:

```bash
export IMG2VID_BIN="$HOME/Downloads/img2vid/.venv/bin/img2vid"
```

The native renderer, written with Python, OpenCV and FFmpeg, works without that dependency. The adapter uses flat animation by default. The actual upstream img2vid CLI was not executed in this sandbox; test on your Mac separately.

## Automated tests

```bash
python -m unittest discover -s tests -v
```

Tests cover account isolation, sign-in/logout, removal of the old Google endpoints, scene editing, ZIP/image input, native MP4 generation and an img2vid adapter with mock executable.

## Upgrading an existing installation without losing your projects

**Do not delete or replace your existing `data/` directory.** It contains SQLite accounts, project metadata, uploaded images and renders.

The easiest visual-only update is to replace these paths in your existing app:

- `frontend/src/main.jsx`
- `frontend/src/style.css`
- `frontend/public/images/` (new folder; copy it in)

To also disable the former Google OAuth API endpoints, replace `backend/auth.py` with this edition's file and reinstall `requirements.txt` if required. The database schema is intentionally left compatible with old versions. The new login page never shows a Google button, even if you only apply the frontend update.

## Implementation notes & limitations

- The moving landing-page story panels are CSS perspective effects on 2D images; they do not mean characters have 3D rigs or actual AI-generated video motion.
- Motion-comic video uses existing illustrations plus camera, transitions and effects; no automatic independent character walking or lipsync.
- Login is local email/password, stored as scrypt password hashes with sessions sent using HttpOnly cookies. Public deployment needs further review of rate limits, account recovery, HTTPS, CSRF protection, etc.
- The exported MP4 supports standard video controls in the editor. This is a single-track scene editor, not a multilayer nonlinear editing tool.
- Browser UI may require a modern desktop browser; scrolling animations respect `prefers-reduced-motion`.

Thankyou