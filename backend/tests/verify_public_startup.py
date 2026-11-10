"""Smoke-test a running instance the way Render's health check would."""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"


def get(path, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status, dict(r.headers), r.read().decode(errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors="ignore")


ok = True


def check(label, condition, detail=""):
    global ok
    ok = ok and bool(condition)
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f"  -> {detail}" if detail else ""))


status, _, body = get("/health")
check("GET /health", status == 200 and json.loads(body).get("status") == "ok", f"{status} {body.strip()}")

status, _, body = get("/health/ready")
check("GET /health/ready (database connected)", status == 200 and "connected" in body, f"{status} {body.strip()}")

for path in ("/", "/login", "/dashboard", "/onboarding"):
    status, headers, body = get(path)
    check(f"GET {path} serves the SPA", status == 200 and "<div id=\"root\">" in body, f"status={status}")

status, headers, body = get("/auth/me")
check("GET /auth/me is unauthenticated (401, not a crash)", status == 401, f"status={status} {body.strip()[:60]}")

status, _, body = get("/challenges/nope")
check("unknown API path returns JSON 404", status == 404 and body.strip().startswith("{"), f"status={status}")

status, headers, _ = get("/health", {"Origin": "https://real-life-rivals.onrender.com"})
allow = {k.lower(): v for k, v in headers.items()}.get("access-control-allow-origin")
check("CORS header present", allow is not None, str(allow))

status, headers, body = get("/")
cache_control = {k.lower(): v for k, v in headers.items()}.get("cache-control")
check("index.html is not cached", "no-cache" in (cache_control or ""), str(cache_control))

print()
print("PUBLIC STARTUP OK" if ok else "PUBLIC STARTUP: FAILURES PRESENT")
sys.exit(0 if ok else 1)
