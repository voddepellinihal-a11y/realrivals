"""Simulate the Render *runtime* environment and exercise the public surface.

Reproduces what Render does when the free web service starts:

    ENVIRONMENT=production
    JWT_SECRET_KEY=<generated>
    DATABASE_URL=<supabase pooler>
    RIVAL1_PASSWORD / RIVAL2_PASSWORD = <generated>
    PORT=<assigned>

then checks the endpoints a visitor (and Render's health check) touches.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = f"http://127.0.0.1:{os.environ.get('PORT', '8001')}"
ORIGIN = "https://real-life-rivals.onrender.com"

results = []


def check(label, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f"  -> {detail}" if detail else ""))


def call(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers or {})
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode(errors="ignore")
            return r.status, dict(r.headers), raw
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors="ignore")


def call_json(method, path, body=None, headers=None):
    status, hdrs, raw = call(method, path, body, headers)
    try:
        return status, hdrs, json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return status, hdrs, raw


print("=" * 70)
print("RENDER RUNTIME SIMULATION")
print("=" * 70)

status, _, body = call_json("GET", "/health")
check("GET /health (Render health check)", status == 200 and body.get("status") == "ok", str(body))

status, _, body = call_json("GET", "/health/ready")
check("GET /health/ready (Supabase connected)", status == 200 and "connected" in str(body), str(body))

status, hdrs, raw = call("GET", "/")
check("GET / serves the SPA", status == 200 and "<div id=\"root\">" in raw, f"status={status}")
check(
    "index.html is not cached (redeploys are picked up)",
    "no-cache" in (hdrs.get("cache-control") or hdrs.get("Cache-Control") or ""),
    hdrs.get("cache-control") or hdrs.get("Cache-Control"),
)

status, hdrs, raw = call("GET", f"/assets/{os.environ.get('ASSET_NAME', '')}") if os.environ.get("ASSET_NAME") else (0, {}, "")
if status:
    check("hashed asset is cached immutably", "immutable" in (hdrs.get("cache-control") or ""), hdrs.get("cache-control"))

for path in ("/login", "/dashboard", "/onboarding"):
    status, _, raw = call("GET", path)
    check(f"GET {path} serves the SPA", status == 200 and "<div id=\"root\">" in raw, f"status={status}")

status, hdrs, body = call_json("GET", "/auth/me")
check("GET /auth/me is 401 when not signed in", status == 401, f"status={status}")

status, hdrs, body = call_json("GET", "/auth/does-not-exist")
check("unknown API path is a JSON 404", status == 404 and isinstance(body, dict), f"status={status}")

status, hdrs, _ = call("GET", "/health", headers={"Origin": ORIGIN})
allow = hdrs.get("access-control-allow-origin") or hdrs.get("Access-Control-Allow-Origin")
check("CORS allows the deployed origin", allow is not None, str(allow))

# --- login with the generated production password -------------------------
email = os.environ.get("TEST_EMAIL", "rival1@realliferivals.com")
password = os.environ.get("TEST_PASSWORD", "")
if password:
    status, hdrs, body = call_json("POST", "/auth/login", {"email": email, "password": password})
    check("POST /auth/login with the production password", status == 200, f"status={status} {str(body)[:80]}")
    cookie = hdrs.get("set-cookie") or hdrs.get("Set-Cookie") or ""
    check("auth cookie is Secure in production", "Secure" in cookie, cookie[:90])
    check("auth cookie is HttpOnly", "HttpOnly" in cookie, cookie[:90])

    cookie_header = cookie.split(";")[0]
    for path in ("/auth/me", "/game/profile", "/routines", "/challenges", "/challenges/versus", "/game/leaderboard"):
        status, _, body = call_json("GET", path, headers={"Cookie": cookie_header})
        check(f"GET {path} while signed in", status == 200, f"status={status}")
else:
    print("[SKIP] login checks (TEST_PASSWORD not set)")

print()
passed = sum(1 for r in results if r)
print(f"{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
