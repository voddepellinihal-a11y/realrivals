"""Log in against a running instance and load the dashboard (public startup check)."""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
EMAIL = sys.argv[2] if len(sys.argv) > 2 else "rival1@realliferivals.com"
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else ""

if not PASSWORD:
    print("usage: verify_login.py <base-url> <email> <password>")
    raise SystemExit(1)

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req, timeout=20) as r:
            raw = r.read().decode()
            try:
                return r.status, (json.loads(raw) if raw else {})
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="ignore")[:200]


status, data = call("POST", "/auth/login", {"email": EMAIL, "password": PASSWORD})
print(f"[{'PASS' if status == 200 else 'FAIL'}] POST /auth/login -> {status}")
if status != 200:
    print("   ", data)
    raise SystemExit(1)

status, data = call("GET", "/auth/me")
user = data.get("user", {}) if isinstance(data, dict) else {}
print(f"[{'PASS' if status == 200 else 'FAIL'}] GET /auth/me -> {status} username={user.get('username')}")
print(f"       level={user.get('level')} xp={user.get('lifetime_xp')} streak={user.get('current_streak')} bmi={user.get('bmi')}")

for path in ("/game/profile", "/routines", "/challenges", "/challenges/versus"):
    status, data = call("GET", path)
    size = len(data) if isinstance(data, list) else "obj"
    print(f"[{'PASS' if status == 200 else 'FAIL'}] GET {path} -> {status} ({size})")

status, _ = call("GET", "/")
print(f"[{'PASS' if status == 200 else 'FAIL'}] GET / -> {status}")
print()
print("LOGIN FLOW OK")
