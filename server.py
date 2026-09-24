from __future__ import annotations

import hmac
import os
import threading
import time
from pathlib import Path

import psycopg
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", "")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "https://ngweichoong.github.io,http://127.0.0.1:5000,http://localhost:5000",
    ).split(",")
    if origin.strip()
]

MAX_NAME_LENGTH = 80
MAX_MESSAGE_LENGTH = 300
MAX_PHONE_LENGTH = 40
MAX_CHILD_AGES_LENGTH = 120
MAX_DIET_LENGTH = 300
MAX_NOTES_LENGTH = 800
RATE_LIMIT_SECONDS = 20
ALLOWED_CAMP_DATES = {
    "2026-10-03",
    "2026-10-10",
    "2026-10-17",
    "2026-10-24",
    "2026-10-31",
}

app = Flask(__name__, static_folder=None)
CORS(
    app,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
    methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

_schema_lock = threading.Lock()
_schema_ready = False
_rate_lock = threading.Lock()
_last_post_by_ip: dict[str, float] = {}


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def ensure_schema():
    global _schema_ready
    if _schema_ready:
        return

    with _schema_lock:
        if _schema_ready:
            return

        last_error = None
        for attempt in range(5):
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            CREATE TABLE IF NOT EXISTS comments (
                                id BIGSERIAL PRIMARY KEY,
                                name VARCHAR(20) NOT NULL,
                                message VARCHAR(300) NOT NULL,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                is_visible BOOLEAN NOT NULL DEFAULT TRUE
                            )
                            """
                        )
                        cur.execute(
                            """
                            CREATE INDEX IF NOT EXISTS comments_created_at_idx
                            ON comments (created_at DESC)
                            """
                        )

                        cur.execute(
                            """
                            CREATE TABLE IF NOT EXISTS camp_registrations (
                                id BIGSERIAL PRIMARY KEY,
                                name VARCHAR(80) NOT NULL,
                                phone VARCHAR(40) NOT NULL,
                                adults SMALLINT NOT NULL CHECK (adults >= 1 AND adults <= 20),
                                children SMALLINT NOT NULL DEFAULT 0 CHECK (children >= 0 AND children <= 20),
                                child_ages VARCHAR(120) NOT NULL DEFAULT '',
                                diet VARCHAR(300) NOT NULL DEFAULT '',
                                notes VARCHAR(800) NOT NULL DEFAULT '',
                                dates TEXT[] NOT NULL,
                                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                                is_visible BOOLEAN NOT NULL DEFAULT TRUE
                            )
                            """
                        )
                        cur.execute(
                            """
                            CREATE INDEX IF NOT EXISTS camp_registrations_created_at_idx
                            ON camp_registrations (created_at DESC)
                            """
                        )
                _schema_ready = True
                return
            except Exception as exc:
                last_error = exc
                if attempt < 4:
                    time.sleep(1.5 * (attempt + 1))

        raise RuntimeError("Unable to initialise database") from last_error


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limited(key: str):
    now = time.monotonic()
    with _rate_lock:
        previous = _last_post_by_ip.get(key)
        if previous is not None and now - previous < RATE_LIMIT_SECONDS:
            return True
        _last_post_by_ip[key] = now

        if len(_last_post_by_ip) > 2000:
            cutoff = now - 3600
            stale = [k for k, stamp in _last_post_by_ip.items() if stamp < cutoff]
            for k in stale:
                _last_post_by_ip.pop(k, None)
    return False


def serialize_comment(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "message": row["message"],
        "created_at": row["created_at"].isoformat(),
    }


def serialize_registration_public(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "dates": row["dates"],
        "created_at": row["created_at"].isoformat(),
    }


def admin_authorized():
    if not ADMIN_TOKEN:
        return False
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    supplied = auth[7:].strip()
    return bool(supplied) and hmac.compare_digest(supplied, ADMIN_TOKEN)


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health():
    try:
        ensure_schema()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return jsonify({"ok": True, "database": "connected"})
    except Exception:
        return jsonify({"ok": False, "database": "unavailable"}), 503


@app.get("/api/comments")
def list_comments():
    ensure_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, message, created_at
                FROM comments
                WHERE is_visible = TRUE
                ORDER BY created_at DESC
                LIMIT 50
                """
            )
            comments = [serialize_comment(row) for row in cur.fetchall()]
    return jsonify({"comments": comments})


@app.post("/api/comments")
def create_comment():
    if not request.is_json:
        return jsonify({"error": "請使用正確的留言格式。"}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "留言格式不正確。"}), 400

    name = payload.get("name")
    message = payload.get("message")
    if not isinstance(name, str) or not isinstance(message, str):
        return jsonify({"error": "請填寫暱稱和留言內容。"}), 400

    name = name.strip()
    message = message.strip()

    if not name or not message:
        return jsonify({"error": "請填寫暱稱和留言內容。"}), 400
    if len(name) > 20:
        return jsonify({"error": "暱稱最多 20 個字元。"}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"留言最多 {MAX_MESSAGE_LENGTH} 個字元。"}), 400
    if rate_limited("comment:" + client_ip()):
        return jsonify({"error": "留言太頻繁，請稍等一下再試。"}), 429

    ensure_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO comments (name, message)
                VALUES (%s, %s)
                RETURNING id, name, message, created_at
                """,
                (name, message),
            )
            comment = serialize_comment(cur.fetchone())

    return jsonify({"comment": comment}), 201


@app.get("/api/registrations/public")
def list_registrations_public():
    ensure_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, dates, created_at
                FROM camp_registrations
                WHERE is_visible = TRUE
                ORDER BY created_at ASC
                LIMIT 200
                """
            )
            registrations = [serialize_registration_public(row) for row in cur.fetchall()]
    return jsonify({"registrations": registrations})


@app.post("/api/registrations")
def create_registration():
    if not request.is_json:
        return jsonify({"error": "請使用正確的報名格式。"}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "報名格式不正確。"}), 400

    name = payload.get("name")
    phone = payload.get("phone")
    child_ages = payload.get("childAges", "")
    diet = payload.get("diet", "")
    notes = payload.get("notes", "")
    dates = payload.get("dates")
    adults = payload.get("adults")
    children = payload.get("children", 0)

    if not isinstance(name, str) or not isinstance(phone, str):
        return jsonify({"error": "請填寫報名代表姓名和聯絡電話。"}), 400
    if not isinstance(child_ages, str) or not isinstance(diet, str) or not isinstance(notes, str):
        return jsonify({"error": "報名文字欄位格式不正確。"}), 400
    if not isinstance(dates, list) or not dates:
        return jsonify({"error": "請至少選擇一個可以參加的星期六。"}), 400

    try:
        adults = int(adults)
        children = int(children)
    except (TypeError, ValueError):
        return jsonify({"error": "參加人數格式不正確。"}), 400

    name = name.strip()
    phone = phone.strip()
    child_ages = child_ages.strip()
    diet = diet.strip()
    notes = notes.strip()
    dates = sorted(set(str(d).strip() for d in dates))

    if not name or not phone:
        return jsonify({"error": "請填寫報名代表姓名和聯絡電話。"}), 400
    if len(name) > MAX_NAME_LENGTH:
        return jsonify({"error": f"姓名最多 {MAX_NAME_LENGTH} 個字元。"}), 400
    if len(phone) > MAX_PHONE_LENGTH:
        return jsonify({"error": f"聯絡電話最多 {MAX_PHONE_LENGTH} 個字元。"}), 400
    if len(child_ages) > MAX_CHILD_AGES_LENGTH:
        return jsonify({"error": "兒童年齡欄位太長。"}), 400
    if len(diet) > MAX_DIET_LENGTH:
        return jsonify({"error": "飲食備註太長。"}), 400
    if len(notes) > MAX_NOTES_LENGTH:
        return jsonify({"error": "其他備註太長。"}), 400
    if adults < 1 or adults > 20 or children < 0 or children > 20:
        return jsonify({"error": "參加人數超出合理範圍。"}), 400
    if any(d not in ALLOWED_CAMP_DATES for d in dates):
        return jsonify({"error": "包含不在本次活動範圍內的日期。"}), 400
    if rate_limited("registration:" + client_ip()):
        return jsonify({"error": "提交太頻繁，請稍等一下再試。"}), 429

    ensure_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO camp_registrations
                    (name, phone, adults, children, child_ages, diet, notes, dates)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, name, dates, created_at
                """,
                (name, phone, adults, children, child_ages, diet, notes, dates),
            )
            registration = serialize_registration_public(cur.fetchone())

    return jsonify({"registration": registration}), 201


@app.delete("/api/comments/<int:comment_id>")
def delete_comment(comment_id: int):
    if not ADMIN_TOKEN:
        return jsonify({"error": "管理功能尚未設定。"}), 503
    if not admin_authorized():
        return jsonify({"error": "管理驗證失敗。"}), 401

    ensure_schema()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM comments WHERE id = %s RETURNING id",
                (comment_id,),
            )
            deleted = cur.fetchone()

    if not deleted:
        return jsonify({"error": "找不到這則留言。"}), 404

    return jsonify({"deleted": deleted["id"]})


@app.get("/")
def home():
    return send_from_directory(ROOT, "index.html")


@app.get("/chapter/<int:chapter>")
def chapter(chapter: int):
    if 1 <= chapter <= 6:
        return send_from_directory(ROOT / "pages", f"chapter{chapter}.html")
    return "Not found", 404


@app.get("/<path:path>")
def static_files(path: str):
    return send_from_directory(ROOT, path)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
