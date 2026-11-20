"""Local email/password authentication with HttpOnly cookie sessions."""
from __future__ import annotations
import hashlib, hmac, os, re, secrets, sqlite3, time, uuid
from contextlib import contextmanager
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix='/api/auth', tags=['auth'])
SESSION_LIFETIME = 60 * 60 * 24 * 7
COOKIE = 'storyframe_session'
DB_PATH: Path | None = None


def init_auth(db_path: Path):
    global DB_PATH
    DB_PATH = db_path
    with sqlite3.connect(DB_PATH) as c:
        c.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password_hash TEXT, google_sub TEXT UNIQUE, created_at REAL NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at REAL NOT NULL)')


@contextmanager
def db():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def present(user):
    return {'id': user['id'], 'name': user['name'], 'email': user['email']}


def require_user(request: Request):
    token = request.cookies.get(COOKIE, '')
    if not token:
        raise HTTPException(401, 'Please sign in')
    digest = hashlib.sha256(token.encode()).hexdigest()
    with db() as c:
        c.execute('DELETE FROM sessions WHERE expires_at < ?', (time.time(),))
        user = c.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?', (digest, time.time())).fetchone()
    if not user:
        raise HTTPException(401, 'Session expired. Please sign in again')
    return present(user)


def current_owner(user=Depends(require_user)):
    return user['id']


def set_session(response: Response, uid: str):
    token = secrets.token_urlsafe(48)
    with db() as c:
        c.execute('INSERT INTO sessions(token_hash,user_id,expires_at) VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), uid, time.time()+SESSION_LIFETIME))
    response.set_cookie(
    COOKIE,
    token,
    max_age=SESSION_LIFETIME,
    httponly=True,
    samesite="none" if os.getenv("STORYFRAME_SECURE_COOKIES", "false").lower() == "true" else "lax",
    secure=os.getenv("STORYFRAME_SECURE_COOKIES", "false").lower() == "true",
    path="/",
)

def pw_hash(password):
    salt = os.urandom(16)
    encoded = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex()+':'+encoded.hex()


def pw_valid(password, stored):
    try:
        salt, digest = stored.split(':', 1)
        check = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1)
        return hmac.compare_digest(check, bytes.fromhex(digest))
    except (TypeError, ValueError):
        return False


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class Register(Credentials):
    name: str = Field(min_length=1, max_length=80)


def email_ok(email):
    return bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email))


@router.post('/register')
def register(data: Register, response: Response):
    email = data.email.strip().lower()
    if not email_ok(email): raise HTTPException(400, 'Enter a valid email address')
    uid = uuid.uuid4().hex
    try:
        with db() as c:
            c.execute('INSERT INTO users(id,name,email,password_hash,created_at) VALUES (?,?,?,?,?)', (uid, data.name.strip(), email, pw_hash(data.password), time.time()))
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'An account with this email already exists')
    set_session(response,uid)
    return {'id':uid,'name':data.name.strip(),'email':email}


@router.post('/login')
def login(data: Credentials, response: Response):
    with db() as c:
        user = c.execute('SELECT * FROM users WHERE email=?', (data.email.strip().lower(),)).fetchone()
    if not user or not user['password_hash'] or not pw_valid(data.password, user['password_hash']):
        raise HTTPException(401, 'Invalid email or password')
    set_session(response, user['id'])
    return present(user)


@router.get('/me')
def me(user=Depends(require_user)):
    return user


@router.post('/logout')
def logout(request: Request,response: Response):
    token=request.cookies.get(COOKIE)
    if token:
        with db() as c:
            c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(
    COOKIE,
    path="/",
    samesite="none" if os.getenv("STORYFRAME_SECURE_COOKIES", "false").lower() == "true" else "lax",
    secure=os.getenv("STORYFRAME_SECURE_COOKIES", "false").lower() == "true",
)
    return {'ok':True}
