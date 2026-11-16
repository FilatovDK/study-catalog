"""SQLite users and two-step password + TOTP login for Study Catalog."""

import base64
import io
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

import pyotp
import qrcode
from PIL import Image, ImageOps, UnidentifiedImageError
from flask import (
    Blueprint, abort, current_app, flash, g, redirect, render_template,
    request, send_file, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


auth = Blueprint("auth", __name__)
Image.MAX_IMAGE_PIXELS = 16_000_000
MAX_AVATAR_BYTES = 2 * 1024 * 1024


def database_path():
    return Path(current_app.config["DATABASE"])


def connect_db():
    if "db" in g:
        return g.db
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        totp_secret TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    columns = {row[1] for row in db.execute("PRAGMA table_info(users)")}
    for name, definition in (
        ("display_name", "TEXT"),
        ("bio", "TEXT"),
        ("favorite_course", "TEXT"),
        ("avatar_file", "TEXT"),
        ("avatar_version", "INTEGER NOT NULL DEFAULT 0"),
    ):
        if name not in columns:
            db.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")
    g.db = db
    return db


def count_users():
    with connect_db() as db:
        return db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()[0]


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)
    return session["csrf_token"]


def valid_csrf():
    supplied = request.form.get("csrf_token", "")
    return bool(supplied) and secrets.compare_digest(supplied, session.get("csrf_token", ""))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def install_auth(app):
    app.config.setdefault("DATABASE", os.environ.get(
        "STUDY_CATALOG_DB", str(Path(app.instance_path) / "users.db")))
    app.config.setdefault("AVATAR_DIR", os.environ.get(
        "STUDY_CATALOG_AVATAR_DIR", str(Path(app.instance_path) / "avatars")))
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    secret_file = Path(os.environ.get(
        "STUDY_CATALOG_SECRET_FILE", str(Path(app.instance_path) / "secret_key")))
    if "STUDY_CATALOG_SECRET_KEY" in os.environ:
        app.secret_key = os.environ["STUDY_CATALOG_SECRET_KEY"]
    else:
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        if not secret_file.exists():
            secret_file.write_text(secrets.token_hex(32), encoding="ascii")
            if os.name != "nt":
                secret_file.chmod(0o600)
        app.secret_key = secret_file.read_text(encoding="ascii").strip()

    app.register_blueprint(auth)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def load_user_and_guard():
        g.user = None
        if "user_id" in session:
            with connect_db() as db:
                g.user = db.execute(
                    "SELECT id, username, display_name, bio, favorite_course, avatar_file, avatar_version "
                    "FROM users WHERE id = ? AND is_active = 1",
                    (session["user_id"],),
                ).fetchone()
            if g.user is None:
                session.clear()
        if request.endpoint in {"health", "metrics_endpoint", "static"}:
            return None
        if request.endpoint and request.endpoint.startswith("auth."):
            return None
        if (os.environ.get("STUDY_CATALOG_PUBLIC_CATALOG") == "1"
                and request.endpoint in {"index", "course_page", "lesson_page"}):
            return None
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return None


def qr_data_uri(secret, username):
    uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="Study Catalog")
    image = qrcode.make(uri)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not valid_csrf():
            abort(400)
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not (3 <= len(username) <= 40) or not username.replace("_", "").isalnum():
            flash("Логин: 3–40 букв, цифр или символов _.", "error")
        elif len(password) < 8:
            flash("Пароль должен содержать не менее 8 символов.", "error")
        else:
            try:
                with connect_db() as db:
                    cursor = db.execute(
                        "INSERT INTO users (username, password_hash, totp_secret) VALUES (?, ?, ?)",
                        (username, generate_password_hash(password), pyotp.random_base32()),
                    )
                    user_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                flash("Этот логин уже занят.", "error")
            else:
                session.clear()
                session["pending_setup_user"] = user_id
                return redirect(url_for("auth.setup_mfa"))
    return render_template("register.html")


@auth.route("/register/mfa", methods=["GET", "POST"])
def setup_mfa():
    user_id = session.get("pending_setup_user")
    if not user_id:
        return redirect(url_for("auth.register"))
    with connect_db() as db:
        user = db.execute(
            "SELECT id, username, totp_secret FROM users WHERE id = ? AND is_active = 0",
            (user_id,),
        ).fetchone()
    if user is None:
        session.clear()
        return redirect(url_for("auth.register"))
    if request.method == "POST":
        if not valid_csrf():
            abort(400)
        code = request.form.get("code", "").strip()
        if code.isascii() and code.isdigit() and len(code) == 6 and pyotp.TOTP(user["totp_secret"]).verify(code):
            with connect_db() as db:
                db.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
            session.clear()
            session["user_id"] = user_id
            return redirect(url_for("index"))
        flash("Неверный код. Проверьте время на телефоне и попробуйте ещё раз.", "error")
    return render_template(
        "setup_mfa.html", username=user["username"], secret=user["totp_secret"],
        qr_data=qr_data_uri(user["totp_secret"], user["username"]),
    )


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not valid_csrf():
            abort(400)
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with connect_db() as db:
            user = db.execute(
                "SELECT id, password_hash, is_active FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if user and user["is_active"] and check_password_hash(user["password_hash"], password):
            session.clear()
            session["pending_login_user"] = user["id"]
            return redirect(url_for("auth.login_mfa"))
        flash("Неверный логин или пароль либо MFA ещё не настроена.", "error")
    return render_template("login.html")


@auth.route("/login/mfa", methods=["GET", "POST"])
def login_mfa():
    user_id = session.get("pending_login_user")
    if not user_id:
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        if not valid_csrf():
            abort(400)
        code = request.form.get("code", "").strip()
        with connect_db() as db:
            user = db.execute(
                "SELECT totp_secret FROM users WHERE id = ? AND is_active = 1",
                (user_id,),
            ).fetchone()
        if user and code.isascii() and code.isdigit() and len(code) == 6 and pyotp.TOTP(user["totp_secret"]).verify(code):
            session.clear()
            session["user_id"] = user_id
            from metrics import MFA_LOGINS
            MFA_LOGINS.inc()
            return redirect(url_for("index"))
        flash("Неверный одноразовый код.", "error")
    return render_template("login_mfa.html")


@auth.post("/logout")
@login_required
def logout():
    if not valid_csrf():
        abort(400)
    session.clear()
    return redirect(url_for("auth.login"))


def avatar_path(user_id):
    return Path(current_app.config["AVATAR_DIR"]) / f"user-{user_id}.jpg"


@auth.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    from app import COURSES

    course_by_slug = {course["slug"]: course for course in COURSES}
    if request.method == "POST":
        if not valid_csrf():
            abort(400)
        display_name = request.form.get("display_name", "").strip()
        bio = request.form.get("bio", "").strip()
        favorite_course = request.form.get("favorite_course", "").strip()
        if not 2 <= len(display_name) <= 50:
            flash("Имя должно содержать от 2 до 50 символов.", "error")
        elif len(bio) > 280:
            flash("Описание не должно превышать 280 символов.", "error")
        elif favorite_course and favorite_course not in course_by_slug:
            flash("Выберите направление из списка.", "error")
        else:
            with connect_db() as db:
                db.execute(
                    "UPDATE users SET display_name = ?, bio = ?, favorite_course = ? WHERE id = ?",
                    (display_name, bio, favorite_course or None, g.user["id"]),
                )
            flash("Профиль сохранён.", "success")
            return redirect(url_for("auth.profile"))
    favorite = course_by_slug.get(g.user["favorite_course"])
    return render_template("profile.html", courses=COURSES, favorite=favorite)


@auth.post("/profile/avatar")
@login_required
def upload_avatar():
    if not valid_csrf():
        abort(400)
    uploaded = request.files.get("avatar")
    if uploaded is None or not uploaded.filename:
        flash("Выберите изображение для загрузки.", "error")
        return redirect(url_for("auth.profile"))
    raw = uploaded.stream.read(MAX_AVATAR_BYTES + 1)
    if len(raw) > MAX_AVATAR_BYTES:
        flash("Фото должно быть меньше 2 МБ.", "error")
        return redirect(url_for("auth.profile"))
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Unsupported image format")
            if source.width * source.height > Image.MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large")
            image = ImageOps.fit(ImageOps.exif_transpose(source).convert("RGB"), (512, 512))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        flash("Нужен корректный файл JPG, PNG или WebP.", "error")
        return redirect(url_for("auth.profile"))

    path = avatar_path(g.user["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.parent.chmod(0o700)
    temporary = path.with_name(path.stem + "-" + secrets.token_hex(6) + ".tmp")
    try:
        image.save(temporary, format="JPEG", quality=86, optimize=True)
        if os.name != "nt":
            temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    with connect_db() as db:
        db.execute(
            "UPDATE users SET avatar_file = ?, avatar_version = avatar_version + 1 WHERE id = ?",
            (path.name, g.user["id"]),
        )
    flash("Фото профиля обновлено.", "success")
    return redirect(url_for("auth.profile"))


@auth.get("/profile/avatar")
@login_required
def avatar_image():
    if not g.user["avatar_file"]:
        abort(404)
    path = avatar_path(g.user["id"])
    if not path.is_file():
        abort(404)
    response = send_file(path, mimetype="image/jpeg", conditional=True, max_age=0)
    response.cache_control.private = True
    return response


@auth.post("/profile/avatar/remove")
@login_required
def remove_avatar():
    if not valid_csrf():
        abort(400)
    with connect_db() as db:
        db.execute(
            "UPDATE users SET avatar_file = NULL, avatar_version = avatar_version + 1 WHERE id = ?",
            (g.user["id"],),
        )
    avatar_path(g.user["id"]).unlink(missing_ok=True)
    flash("Фото профиля удалено.", "success")
    return redirect(url_for("auth.profile"))
