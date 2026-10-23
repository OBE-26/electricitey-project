"""Shared course configuration and password-gated, server-graded theory tests."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

COURSES = {"hvac": "קורס מיזוג וקירור", "security": "קורס מיגון", "mobile": "קורס סלולר"}
ISRAEL = ZoneInfo("Asia/Jerusalem")


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    return {"salt": salt, "hash": hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000).hex()}


def password_matches(password, stored):
    try:
        return hmac.compare_digest(password_hash(password, stored["salt"])["hash"], stored["hash"])
    except (KeyError, TypeError, ValueError):
        return False


def code_active(code, today=None):
    today = today or datetime.now(ISRAEL).date()
    return code.get("active") is True and (not code.get("expires_on") or today <= date.fromisoformat(code["expires_on"]))


class ConfigStore:
    """One server-wide store; optionally back it with a private GitHub file."""

    def __init__(self, path=None, repository="", token=""):
        self.path = Path(path or os.environ.get("DC_COURSE_CONFIG_PATH", str(Path.home() / ".local/share/electricity/course_admin.json")))
        self.repository, self.token = repository, token
        self.lock = threading.RLock()
        self._cached = None
        self._cached_at = 0

    def _request(self, suffix, payload=None):
        request = urllib.request.Request(
            f"https://api.github.com/repos/{self.repository}{suffix}",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json", "User-Agent": "electricity-courses"},
            method="PUT" if payload is not None else "GET")
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)

    def _remote(self):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repository):
            raise ValueError("Invalid storage repository")
        if not self.token or not self.token.isascii() or self.token.strip().upper() in {"XXX", "PASTE_YOUR_GITHUB_TOKEN_HERE"}:
            raise ValueError("יש להחליף את טקסט הדוגמה ב־course_admin.storage_token בטוקן GitHub אמיתי ב־Streamlit Secrets, עם הרשאת Contents: Read and write למאגר הפרטי.")
        if self._request("").get("private") is not True:
            raise ValueError("Course access configuration requires a private repository")
        try:
            result = self._request("/contents/course-admin.json")
            return json.loads(base64.b64decode(result["content"])), result["sha"]
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None, None
            raise

    @staticmethod
    def _default():
        return {"version": 1, "names": dict(COURSES), "passwords": [], "signing_key": secrets.token_hex(32)}

    def _write_local(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.path.with_suffix(".tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)
        os.replace(temporary, self.path)

    def read(self, fresh=False):
        with self.lock:
            if self._cached is not None and not fresh and time.monotonic() - self._cached_at < 10:
                return self._cached
            local = json.loads(self.path.read_text()) if self.path.exists() else None
            if self.repository:
                remote, sha = self._remote()
                if remote is None:
                    remote = local or self._default()
                    self._request("/contents/course-admin.json", {"message": "Initialize course administration", "content": base64.b64encode(json.dumps(remote, ensure_ascii=False).encode()).decode()})
                data = remote
            else:
                data = local or self._default()
            self._write_local(data)
            self._cached, self._cached_at = data, time.monotonic()
            return data

    def save(self, names, rows):
        with self.lock:
            current = self.read(fresh=True)
            if set(names) != set(COURSES) or any(not isinstance(v, str) or not 2 <= len(v.strip()) <= 60 for v in names.values()):
                raise ValueError("יש להזין שם של 2–60 תווים לכל קורס.")
            if not isinstance(rows, list) or len(rows) > 100:
                raise ValueError("אפשר להגדיר עד 100 סיסמאות.")
            existing = {row["id"]: row for row in current["passwords"]}
            saved, used = [], set()
            for row in rows:
                identifier = row.get("id") or secrets.token_hex(12)
                if identifier in used:
                    raise ValueError("סיסמה מופיעה פעמיים ברשימה.")
                used.add(identifier)
                label, expiry = row.get("label", "").strip(), row.get("expires_on", "")
                if not 1 <= len(label) <= 60:
                    raise ValueError("יש להזין שם לכל סיסמה.")
                if expiry:
                    date.fromisoformat(expiry)
                plain = row.get("password", "")
                if not isinstance(plain, str) or plain and not 4 <= len(plain) <= 128:
                    raise ValueError("סיסמה חדשה צריכה לכלול 4–128 תווים.")
                if plain and (any(password_matches(plain, item) for item in saved) or any(
                    other is not row and (
                        hmac.compare_digest(plain.encode(), other["password"].encode())
                        if isinstance(other.get("password"), str) and other["password"]
                        else password_matches(plain, existing.get(other.get("id"), {})))
                    for other in rows)):
                    raise ValueError("יש להזין סיסמאות שונות.")
                hashed = password_hash(plain) if plain else {k: existing.get(identifier, {}).get(k) for k in ("salt", "hash")}
                if not hashed["hash"]:
                    raise ValueError("יש להזין סיסמה עבור הרשומה החדשה.")
                # Shared classroom access codes are recoverable for the owner,
                # by explicit request. Only authenticated admin responses expose
                # this value; student authentication still checks the hash.
                display_password = plain or existing.get(identifier, {}).get("display_password")
                saved.append({"id": identifier, "label": label, "expires_on": expiry,
                              "active": row.get("active") is True, **hashed,
                              **({"display_password": display_password} if display_password else {})})
            data = {**current, "names": {k: v.strip() for k, v in names.items()}, "passwords": saved}
            if self.repository:
                _, sha = self._remote()
                payload = {"message": "Update course names and theory access", "content": base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()}
                if sha:
                    payload["sha"] = sha
                self._request("/contents/course-admin.json", payload)
            self._write_local(data)
            self._cached, self._cached_at = data, time.monotonic()
            return self.public(admin=True)

    def public(self, admin=False):
        data = self.read()
        result = {"names": data["names"]}
        if admin:
            result["passwords"] = [
                {**{k: row[k] for k in ("id", "label", "expires_on", "active")},
                 "status": "disabled" if not row["active"] else "active" if code_active(row) else "expired",
                 "password_text": row.get("display_password")}
                for row in data["passwords"]]
            result["durable"] = bool(self.repository)
        return result

    def update(self, *, names=None, password=None, delete_id=None):
        """Edit one part of the latest saved settings without replacing others."""
        with self.lock:
            current = self.read(fresh=True)
            rows = [dict(row) for row in current["passwords"]]
            if password is not None:
                if not isinstance(password, dict):
                    raise ValueError("פרטי הסיסמה אינם תקפים.")
                identifier = password.get("id")
                if identifier:
                    if identifier not in {row["id"] for row in rows}:
                        raise ValueError("הסיסמה אינה קיימת עוד. לחצו על רענון הרשימה.")
                    rows = [password if row["id"] == identifier else row for row in rows]
                else:
                    rows.append(password)
            if delete_id is not None:
                if delete_id not in {row["id"] for row in rows}:
                    raise ValueError("הסיסמה אינה קיימת עוד. לחצו על רענון הרשימה.")
                rows = [row for row in rows if row["id"] != delete_id]
            return self.save(current["names"] if names is None else names, rows)


def select_questions(pool, seen=(), previous=(), count=20, rng=None):
    rng = rng or secrets.SystemRandom()
    previous = set(previous)
    seen_at = {identifier: index for index, identifier in enumerate(seen)}
    outside = [q for q in pool if q["id"] not in previous]
    fresh = [q for q in outside if q["id"] not in seen_at]
    rng.shuffle(fresh)
    chosen = fresh[:count]
    older = [q for q in outside if q["id"] in seen_at]
    # Exhaust unseen questions first, then rotate through the oldest seen items.
    rng.shuffle(older)
    older.sort(key=lambda q: seen_at[q["id"]])
    chosen += older[:count - len(chosen)]
    missing = count - len(chosen)
    if missing > 5:
        raise ValueError("אין במאגר מספיק שאלות להגרלה לפי מגבלת החזרות.")
    if missing:
        chosen += rng.sample([q for q in pool if q["id"] in previous], missing)
    if len(chosen) != count:
        raise ValueError("אין במאגר מספיק שאלות למבחן.")
    rng.shuffle(chosen)
    return chosen


def remap_choice_references(text, labels):
    if not re.search(r"תשובות|אפשרויות המוזכרות", text):
        return text
    return re.sub(r"(?<![א-ת])([אבגד])(?=[׳'\"״)]|\s+נכונות)", lambda match: labels.get(match[1], match[1]), text)


class CourseService:
    def __init__(self, store, bank_path, admin_password="210592"):
        self.store, self.bank_path, self.admin_password = store, Path(bank_path), admin_password
        raw = self.bank_path.read_bytes()
        self.version = hashlib.sha256(raw).hexdigest()[:16]
        data = json.loads(raw)
        self.pool = [{**q, "exam_title": exam["title"]} for exam in data["exams"] for q in exam["questions"]]
        self.by_id = {q["id"]: q for q in self.pool}
        if len(self.by_id) != len(self.pool) or any(q.get("correct_choice_id") not in {c["id"] for c in q["choices"]} for q in self.pool):
            raise ValueError("Invalid question bank or answer key")

    def _sign(self, data):
        encoded = base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).decode()
        signature = hmac.new(bytes.fromhex(self.store.read()["signing_key"]), encoded.encode(), "sha256").hexdigest()
        return encoded + "." + signature

    def _verify(self, token):
        encoded, signature = token.rsplit(".", 1)
        expected = hmac.new(bytes.fromhex(self.store.read()["signing_key"]), encoded.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("המבחן השמור אינו תקף. יש להגריל מבחן חדש.")
        data = json.loads(base64.urlsafe_b64decode(encoded))
        if data.get("version") != self.version:
            raise ValueError("מאגר השאלות עודכן. יש להגריל מבחן חדש.")
        return data

    def _authorized(self, event, session, admin=False):
        saved = session.get("course_admin" if admin else "course_theory", {})
        if not saved.get("token") or not hmac.compare_digest(str(event.get("token", "")), saved["token"]):
            return False
        if admin:
            return time.time() < saved.get("until", 0)
        code = next((row for row in self.store.read(fresh=True)["passwords"] if row["id"] == saved.get("code_id")), None)
        return bool(code and code_active(code) and code["hash"] == saved.get("hash"))

    @staticmethod
    def _rate_limit(session, kind):
        now = time.time()
        attempts = [stamp for stamp in session.get(kind, []) if now - stamp < 60]
        if len(attempts) >= 8:
            raise ValueError("בוצעו ניסיונות רבים. נסו שוב בעוד דקה.")
        session[kind] = attempts + [now]

    def _question(self, q, order):
        choices = {c["id"]: c for c in q["choices"]}
        labels = {choices[identifier]["label"]: "אבגד"[index] for index, identifier in enumerate(order)}
        result = {"id": q["id"], "text": remap_choice_references(q["text"], labels), "choices": [
            {"id": identifier, "label": "אבגד"[index], "text": remap_choice_references(choices[identifier]["text"], labels)}
            for index, identifier in enumerate(order)]}
        if q.get("math_latex"):
            result["math_latex"] = q["math_latex"]
        if q.get("figure"):
            figure = q["figure"]
            path = self.bank_path.parent / figure.get("svg_path", figure["path"])
            mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
            result["figure"] = {"src": f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode(), "alt": figure.get("alt", "תרשים המעגל")}
        return result

    def _admin_config(self):
        try:
            self.store.read(fresh=True)
            return self.store.public(admin=True)
        except (ValueError, OSError, urllib.error.URLError) as error:
            if isinstance(error, ValueError):
                message = str(error)
            elif isinstance(error, urllib.error.HTTPError) and error.code in (401, 403, 404):
                message = "לא ניתן לגשת למאגר השמירה הפרטי. בדקו ב־Streamlit Secrets את course_admin.storage_repository ואת storage_token, ואת הרשאת Contents: Read and write של הטוקן למאגר הזה."
            else:
                message = "החיבור לשמירה אינו זמין כרגע. אפשר לבדוק את התרגילים ב־QA ולנסות לרענן את החיבור בהמשך."
            # Authentication is independent of storage. Do not invent an empty
            # password list or fall back to another store during an outage.
            return {"names": dict(COURSES), "unavailable": True, "storage_message": message}

    def handle(self, event, session):
        action = event.get("action")
        try:
            if action == "admin_login":
                self._rate_limit(session, "course_admin_attempts")
                if not hmac.compare_digest(str(event.get("password", "")), self.admin_password):
                    raise ValueError("סיסמה שגויה. נסו שוב.")
                token = secrets.token_urlsafe(24)
                session["course_admin"] = {"token": token, "until": time.time() + 8 * 3600}
                return {"ok": True, "token": token, "config": self._admin_config(),
                        "capabilities": {"qa_theory": True, "password_management": True}}
            if action in {"admin_refresh", "admin_names_save", "admin_password_save", "admin_password_delete"}:
                if not self._authorized(event, session, admin=True):
                    return {"ok": False, "unauthorized": True, "message": "נדרשת כניסה מחדש למצב בדיקות."}
                if action == "admin_refresh":
                    config = self._admin_config()
                    message = config.get("storage_message", "הרשימה נטענה מחדש מהשמירה.")
                elif action == "admin_names_save":
                    config = self.store.update(names=event.get("names", {}))
                    message = "שמות הקורסים נשמרו."
                elif action == "admin_password_save":
                    config = self.store.update(password=event.get("password", {}))
                    message = "הסיסמה והשינויים שלה נשמרו."
                else:
                    config = self.store.update(delete_id=event.get("password_id", ""))
                    message = "הסיסמה נמחקה."
                return {"ok": True, "config": config, "message": message}
            if action == "admin_save":
                if not self._authorized(event, session, admin=True):
                    return {"ok": False, "unauthorized": True, "message": "נדרשת כניסה מחדש למצב בדיקות."}
                return {"ok": True, "config": self.store.save(event.get("names", {}), event.get("passwords", [])), "message": "שמות הקורסים והסיסמאות נשמרו לכל המשתמשים."}
            if action == "admin_logout":
                if not self._authorized(event, session, admin=True):
                    return {"ok": False, "unauthorized": True, "message": "נדרשת כניסה מחדש למצב בדיקות."}
                session.pop("course_admin", None)
                return {"ok": True}
            if action == "exam_login":
                self._rate_limit(session, "course_exam_attempts")
                password = event.get("password", "")
                if not isinstance(password, str) or len(password) > 128:
                    raise ValueError("סיסמה לא תקפה.")
                code = next((row for row in self.store.read(fresh=True)["passwords"] if code_active(row) and password_matches(password, row)), None)
                if code is None:
                    raise ValueError("הסיסמה שגויה או שתוקפה הסתיים.")
                token = secrets.token_urlsafe(24)
                session["course_theory"] = {"token": token, "code_id": code["id"], "hash": code["hash"]}
                return {"ok": True, "token": token, "count": len(self.pool)}
            if action in {"exam_new", "exam_resume", "exam_submit", "admin_exam_new", "admin_exam_resume", "admin_exam_submit"}:
                qa = action.startswith("admin_exam_") or event.get("qa") is True
                action = action.removeprefix("admin_")
                if not self._authorized(event, session, admin=qa):
                    return {"ok": False, "unauthorized": True, "message": "פג תוקף כניסת המנהל. צאו מ־QA והיכנסו אליו שוב." if qa else "נדרשת סיסמה תקפה כדי להמשיך למבחן."}
                if action == "exam_new":
                    seen = [s for s in event.get("seen", []) if isinstance(s, str)][-len(self.pool):]
                    previous = [s for s in event.get("previous", []) if isinstance(s, str)][:20]
                    selected = select_questions(self.pool, seen, previous)
                    orders = {q["id"]: secrets.SystemRandom().sample([c["id"] for c in q["choices"]], len(q["choices"])) for q in selected}
                    exam = {"version": self.version, "id": secrets.token_hex(12), "ids": [q["id"] for q in selected], "orders": orders, "qa": qa}
                    signed = self._sign(exam)
                else:
                    signed = str(event.get("exam", ""))
                    exam = self._verify(signed)
                    if exam.get("qa", False) != qa:
                        raise ValueError("מבחן בדיקה זמין רק במצב QA. יש להגריל מבחן חדש.")
                questions = [self._question(self.by_id[identifier], exam["orders"][identifier]) for identifier in exam["ids"]]
                result = {"ok": True, "exam": signed, "id": exam["id"], "questions": questions, "qa": qa}
                if action == "exam_submit":
                    answers = event.get("answers", {})
                    if not isinstance(answers, dict) or set(answers) - set(exam["ids"]):
                        raise ValueError("התשובות שנשלחו אינן תואמות למבחן.")
                    for q in questions:
                        choice = answers.get(q["id"])
                        if choice is not None and choice not in {c["id"] for c in q["choices"]}:
                            raise ValueError("בחירה לא תקפה.")
                        q.update(correct_choice_id=self.by_id[q["id"]]["correct_choice_id"], selected_choice_id=choice)
                    result["correct"] = sum(q["correct_choice_id"] == q["selected_choice_id"] for q in questions)
                    result["total"] = len(questions)
                    result["finished_at"] = datetime.now(ISRAEL).isoformat()
                return result
            raise ValueError("פעולה לא מוכרת.")
        except (ValueError, KeyError, TypeError, OSError, urllib.error.URLError) as error:
            message = str(error) if isinstance(error, ValueError) else "הפעולה לא הושלמה. אפשר לנסות שוב."
            return {"ok": False, "message": message}
