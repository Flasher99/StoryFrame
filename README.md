# StoryFrame — img2vid Integration MVP

A runnable, local-first storybook-to-motion-comic web application. Exactly four screens: landing, demo sign-in, project dashboard, and single-track scene editor. Folder/ZIP input, local MP4 output. Tested with the two supplied cartoon illustrations.

## Supported effects
- **Camera:** push-in, pull-out, left/right pan, up/down tracking, static.
- **Transitions:** cut, dissolve, slide.
- **Atmosphere:** falling leaves, floating particles, none.
- Frame-based H.264 MP4, free local rendering, no paid API or dedicated GPU.

## macOS quick start

Requires Python 3.10+, Node.js 18+, and FFmpeg (`brew install ffmpeg`).

**Terminal 1 — API:**

```bash
cd storyframe_mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

**Terminal 2 — web:**

```bash
cd storyframe_mvp/frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173**, sign in with a display name, click **Try sample story** (or upload images, a folder, or a ZIP), edit scene settings and click **Render MP4**. Wait until rendering finishes, then click **Watch rendered video** or **Download MP4**.

## Use the real img2vid renderer

StoryFrame does **not** bundle or pretend to include the upstream `img2vid` source. It detects your separately installed [img2vid CLI](https://github.com/mrityunjay/img2vid), builds a storyboard matching its documented JSON schema, invokes `img2vid render`, then overlays atmospheric effects on its MP4. All editable scene settings are saved in SQLite.

If you previously installed it in `~/Downloads/img2vid/.venv/bin/img2vid`, StoryFrame detects it automatically. Otherwise install it in a separate terminal:

```bash
cd ~/Downloads
git clone https://github.com/mrityunjay/img2vid.git
cd img2vid
./install.sh --core
.venv/bin/img2vid --help
```

**Alternatively** set `IMG2VID_BIN` before running FastAPI to the full path to the executable, for example:

```bash
export IMG2VID_BIN="$HOME/Downloads/img2vid/.venv/bin/img2vid"
uvicorn backend.app:app --reload --port 8000
```

Check detection at **http://127.0.0.1:8000/api/health**; `img2vidAvailable` should be `true`. With the editor's **Auto** engine, StoryFrame prefers external img2vid when installed. With **Built-in fallback**, it always renders using OpenCV + FFmpeg. If you select **img2vid** explicitly when it is missing, you will get a readable error instead of a silent fallback.

### Important notes about interoperability
- The adapter uses `img2vid render storyboard.json -o ... --resolution 540`, as documented by upstream on Nov 18 2026. The installed version could differ; the actual upstream CLI needs to be tested on your Mac.
- Upstream scenes include **outgoing** transition settings; StoryFrame's editor controls **incoming** transitions. The adapter translates between them.
- This MVP uses img2vid's **flat motion** (`depth: false`, `animate: false`); no large AI models or downloaded depth weights are needed.
- Upstream may overlap transition durations, making the final video marginally shorter than the sum of nominal scene lengths; atmospheric overlays use approximate scene boundaries.
- If upstream rendering fails, select the built-in renderer rather than attempting an untested automatic rerender.
- The CLI and its dependencies are installed independently; review upstream project/model licenses before distributing an integrated commercial product.

## Architecture

`frontend/` (React + Vite UI) → `backend/app.py` (FastAPI, persistence, uploads) → `backend/img2vid_bridge.py` (upstream storyboard, subprocess) → `backend/effects.py` (post-processing overlay) → FFmpeg H.264.

Fallback `backend/app.py` also contains the existing OpenCV frame renderer and doesn't require img2vid.

## Run tests

```bash
python -m unittest discover -s tests -v
```

Tests cover upload/order, ZIP input, permissions isolation, scene edits, native MP4 render, storyboard mapping, and a **mock executable** exercising the img2vid adapter + atmospheric effects. The actual third-party CLI cannot be run in this packaging environment because cloning GitHub is unavailable here; that test requires your Mac installation.

## Explicit MVP limitations

- Local demo identity is **not** secure authentication; don't expose the application publicly.
- No walking, lip-sync, skeletal animation, or AI-generated moving characters.
- Preview initially displays a still image; the **Watch rendered video** button plays the final moving MP4 after rendering.
- No automatic natural-language story analysis or speech synthesis.
- External img2vid is optional; particles/leaves are implemented in StoryFrame's own post-processing, not in img2vid.
- No completed frontend browser smoke test in this packaging environment. Verify `npm install && npm run dev` locally.
- Scene duration is editable but not inferred from story events.

---

## Updated authentication and final-video preview

### New login & account creation

StoryFrame now has a **Sign in** and **Create account** panel. New local accounts are stored in the SQLite database (`data/storyframe.sqlite`). Passwords are salted and hashed with scrypt. Sessions use secure random bearer tokens stored only as hashes in the database and sent in HttpOnly, SameSite=Lax cookies. Project and video API access is restricted to the signed-in user, rather than relying on a display-name query parameter.

1. Start the FastAPI backend and Vite frontend with the commands above.
2. Open `http://127.0.0.1:5173/#/login`.
3. Choose **Create account**, enter your name, email, and a password of at least eight characters.
4. Subsequent visits can use **Sign in** with email/password. Use **Sign out** when finished.

The older demo-only display-name identity has been replaced: existing demo projects from the previous version are **not automatically migrated** into a real user account. This avoids accidentally exposing another user's work. Do not deploy this MVP as a public production service without further security review (HTTPS, CSRF controls, rate limiting, email confirmation, password reset, backups and monitoring).

### Enable Google / Gmail sign-in

The Google option uses Google's identity system. It cannot be activated just by installing the repository; you must configure a **Google OAuth 2.0 Web application client ID**:

1. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials), set up the OAuth consent configuration and create an **OAuth Client ID** of type **Web application**.
2. Under **Authorized JavaScript origins**, add both `http://127.0.0.1:5173` and `http://localhost:5173` (only origins that you actually use are required). Google Identity Services requires the correct origin to be registered. For hosted use, register your HTTPS domain.
3. Set your backend environment variable **before** running Uvicorn:

   ```bash
   export GOOGLE_CLIENT_ID="YOUR_WEB_CLIENT_ID.apps.googleusercontent.com"
   uvicorn backend.app:app --reload --port 8000
   ```

4. Restart the frontend and refresh the login page. **Continue with Google** should display a working Google sign-in button. The server validates the ID token against the configured client ID. The client ID is public configuration, **not** a secret. Do not place a Google client secret in frontend source code.

If this variable is not set, Google sign-in is visibly marked **Not configured**. The account creation and email/password login continue to work without Google Cloud setup or payment. A user registered via email/password should sign in with their password; this version does not automatically link Google identity to an existing password account with the same email.

### Final preview before download

After **Render MP4**, StoryFrame keeps the editor open while processing and refreshes the project's status. When the video is ready, the editor automatically switches its large preview screen to the **actual rendered MP4** with playback controls. The **Download MP4** button appears in the final preview panel after rendering succeeds. Changing an animation property invalidates the previous render and requires a new export.

### Testing

```bash
python -m unittest discover -s tests -v
```

Automated tests check account creation, login/logout, per-user project isolation, upload and timeline edits, native MP4 generation, and the mocked img2vid adapter. The Google cloud sign-in flow requires a real Google client ID and browser interaction to test manually. The frontend JSX was syntax-checked, but installing and building npm dependencies in the sandbox was not completed; please run `cd frontend && npm install && npm run build` locally.
