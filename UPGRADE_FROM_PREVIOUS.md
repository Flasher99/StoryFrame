# Upgrade your working StoryFrame installation

Your existing projects and user accounts live in `data/`. **Do not overwrite or delete that directory.**

Recommended steps:

1. Make a backup copy of your current `storyframe_mvp` folder.
2. From this new edition, copy these files into the corresponding paths of your working installation:
   - `frontend/src/main.jsx`
   - `frontend/src/style.css`
   - `frontend/public/images/icecream.jpg` and `frontend/public/images/park.jpg`
3. Optional but recommended if you want to disable Google login on the server too: copy `backend/auth.py`. (No database migration needed.)
4. From your existing frontend folder, run `npm install`, then `npm run dev`.
5. Leave your backend running if you changed only the frontend. Restart Uvicorn if you changed `backend/auth.py`.
6. Open `http://127.0.0.1:5173` and verify login, project cards, final preview and MP4 export.

There are no new frontend dependencies. The animation in the landing page uses standard CSS/React. Font loading uses Google Fonts when available, with local system/serif fallbacks.

**Note:** Accounts created using Google sign-in alone will no longer have a login route after disabling the backend Google integration. Password-based accounts remain usable. If you have Google-only accounts you still need, don't remove the backend route until you set up an alternative sign-in path for those users.
