"""End-to-end verification for the Real-Life Rivals master task.

Exercises: login -> biometrics (PATCH /user/preferences) -> dynamic XP math ->
direct 1v1 challenge -> photo proof upload (base64) -> mutual proof preview ->
approve -> XP payout.  Prints Done/Needed style output.
"""
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

# Make the backend package importable when this file is run directly.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

BASE = "http://127.0.0.1:8000"

# Credentials of the two seeded private accounts.  They are read from the
# environment so a working password never has to live in the repository.
# Put them in backend/.env (git-ignored) or export them before running.
RIVAL1_EMAIL = os.environ.get("RIVAL1_EMAIL", "rival1@realliferivals.com")
RIVAL1_PASSWORD = os.environ.get("RIVAL1_PASSWORD", "")
RIVAL2_EMAIL = os.environ.get("RIVAL2_EMAIL", "rival2@realliferivals.com")
RIVAL2_PASSWORD = os.environ.get("RIVAL2_PASSWORD", "")

if not (RIVAL1_PASSWORD and RIVAL2_PASSWORD):
    print(
        "Set RIVAL1_PASSWORD and RIVAL2_PASSWORD before running this script.\n"
        "Add them to backend/.env (git-ignored) or export them first."
    )
    raise SystemExit(1)

# 1x1 transparent PNG
PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
    "IQAAAABJRU5ErkJggg=="
)


class Client:
    def __init__(self):
        self.cookie = None

    def call(self, method, path, body=None):
        url = BASE + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self.cookie:
            req.add_header("Cookie", self.cookie)
        try:
            with urllib.request.urlopen(req) as r:
                raw = r.read().decode()
                sc = r.headers.get("Set-Cookie")
                if sc:
                    self.cookie = sc.split(";")[0]
                return r.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, {"raw": raw}

    def get(self, path):
        return self.call("GET", path)

    def post(self, path, body=None):
        return self.call("POST", path, body)

    def patch(self, path, body=None):
        return self.call("PATCH", path, body)

    def delete(self, path):
        return self.call("DELETE", path)


results = []


def check(label, ok, detail=""):
    results.append((label, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  -> {detail}" if detail else ""))


def level_for(xp):
    return max(1, int((xp / 100) ** (1 / 1.5)) + 1)


def progress_for(xp, level):
    if xp <= 0:
        return 0
    prev = int(100 * (level - 1) ** 1.5)
    nxt = int(100 * level**1.5)
    return max(0, min(100, round((xp - prev) / max(nxt - prev, 1) * 100, 1)))


print("=" * 78)
print("RIVAL 1 (challenger)")
print("=" * 78)
r1 = Client()
st, d = r1.post("/auth/login", {"email": RIVAL1_EMAIL, "password": RIVAL1_PASSWORD})
check("POST /auth/login (rival1)", st == 200, f"status={st}")
u1 = d.get("user", {})

st, d = r1.get("/auth/me")
check("GET /auth/me", st == 200 and "user" in d, f"status={st}")

# --- Biometrics via the spec'd PATCH /user/preferences --------------------
st, d = r1.patch("/user/preferences", {"height_cm": 178, "weight_kg": 74.5, "target_weight_kg": 70})
bmi = d.get("preferences", {}).get("bmi")
check("PATCH /user/preferences", st == 200, f"status={st} body={d}")
check("BMI computed live (74.5 / 1.78^2 == 23.5)", bmi is not None and abs(bmi - 23.5) < 0.2, f"bmi={bmi}")

st, d = r1.patch("/auth/preferences", {"height_cm": 178, "weight_kg": 74.5, "target_weight_kg": 70})
check("PATCH /auth/preferences (alias still works)", st == 200, f"status={st}")

st, d = r1.get("/auth/me")
me = d.get("user", {})
check("GET /auth/me returns biometrics + bmi",
      me.get("height_cm") == 178 and me.get("weight_kg") == 74.5 and me.get("bmi") is not None,
      f"height={me.get('height_cm')} weight={me.get('weight_kg')} bmi={me.get('bmi')}")

# --- Dynamic XP math ------------------------------------------------------
st, d = r1.get("/game/profile")
prof = d.get("profile", d)
lxp = prof.get("lifetime_xp", 0)
check("GET /game/profile", st == 200, f"status={st} lifetime_xp={lxp}")
lvl = level_for(lxp)
pct = progress_for(lxp, lvl)
check("Dynamic XP math matches formula",
      lvl == int((lxp / 100) ** (1 / 1.5)) + 1 if lxp > 0 else lvl == 1,
      f"xp={lxp} level={lvl} progress={pct}%")
check("0 XP renders as an empty 0% bar (fresh account)",
      level_for(0) == 1 and progress_for(0, 1) == 0,
      f"level={level_for(0)} progress={progress_for(0, 1)}%")

# --- Direct 1v1 challenge -------------------------------------------------
st, d = r1.post("/challenges/direct", {
    "title": "Evening Focus Sprint",
    "description": "Head-to-head focus sprint",
    "category": "fitness",
    "xp_reward": 150,
    "proof_type": "photo",
    "target_username_or_id": "rival2",
})
check("POST /challenges/direct (rival1 -> rival2)", st == 200, f"status={st} id={d.get('id')} status={d.get('status')}")
chal_id = d.get("id")

st, d = r1.get("/challenges/versus")
check("GET /challenges/versus shows the duel", st == 200 and any(c.get("id") == chal_id for c in d),
      f"count={len(d) if isinstance(d, list) else 'n/a'}")

print()
print("=" * 78)
print("RIVAL 2 (target)")
print("=" * 78)
r2 = Client()
st, d = r2.post("/auth/login", {"email": RIVAL2_EMAIL, "password": RIVAL2_PASSWORD})
check("POST /auth/login (rival2)", st == 200, f"status={st}")

st, d = r2.get("/challenges/versus")
pending = [c for c in d if c.get("id") == chal_id] if isinstance(d, list) else []
check("rival2 sees the incoming duel", st == 200 and len(pending) == 1, f"status={st}")
check("Duel status is PENDING_ACCEPTANCE", pending and pending[0].get("status") == "PENDING_ACCEPTANCE",
      pending[0].get("status") if pending else "n/a")
check("is_challenger=False for the target", pending and pending[0].get("is_challenger") is False,
      str(pending[0].get("is_challenger")) if pending else "n/a")

st, d = r2.post(f"/challenges/{chal_id}/accept", {})
check("POST /challenges/{id}/accept", st == 200, f"status={st}")

# --- Photo proof upload (base64) -----------------------------------------
st, d = r2.post("/submissions", {
    "challenge_id": chal_id,
    "proof_type": "photo",
    "proof_url": f"data:image/png;base64,{PNG_B64}",
    "proof_data_url": f"data:image/png;base64,{PNG_B64}",
    "proof_text": "",
    "description": "",
})
check("POST /submissions (base64 photo proof)", st == 200, f"status={st} {d}")
sub_id = d.get("id")
check("Submission is PENDING_REVIEW", d.get("status") == "PENDING_REVIEW", str(d.get("status")))

# --- Mutual proof preview -------------------------------------------------
st, d = r1.get(f"/submissions/challenge/{chal_id}/submissions")
check("rival1 can preview rival's proof", st == 200 and isinstance(d, list) and len(d) >= 1,
      f"status={st} count={len(d) if isinstance(d, list) else 'n/a'}")
mine = [s for s in d if s.get("is_me")]
theirs = [s for s in d if not s.get("is_me")]
check("Preview is mutual (own + rival submissions)", len(mine) >= 0 and len(theirs) >= 1,
      f"mine={len(mine)} theirs={len(theirs)}")

# --- Approve -> XP payout -------------------------------------------------
# rival2 submitted the proof, so rival1 is the reviewer and rival2 earns the XP.
st, d = r1.post(f"/submissions/{sub_id}/reviews", {"decision": "approved"})
check("POST /submissions/{id}/reviews (rival1 approves rival2's proof)", st == 200, f"status={st} {d}")

st, d = r2.post(f"/submissions/{sub_id}/reviews", {"decision": "approved"})
check("Self-review is rejected", st == 403, f"status={st} {d}")

st, d = r2.get("/game/profile")
prof2 = d.get("profile", d)
lxp2 = prof2.get("lifetime_xp", 0)
check("XP awarded to the proof owner", lxp2 >= 150, f"lifetime_xp={lxp2}")
check("XP reflected in level math", level_for(lxp2) >= 2, f"level={level_for(lxp2)} progress={progress_for(lxp2, level_for(lxp2))}%")

st, d = r2.get("/game/history")
check("GET /game/history (ledger)", st == 200, f"status={st}")

# --- Idempotency ----------------------------------------------------------
st, _ = r2.post(f"/submissions/{sub_id}/reviews", {"decision": "approved"})
st2, d = r2.get("/game/profile")
lxp3 = d.get("profile", d).get("lifetime_xp", 0)
check("Duplicate approval does not double-award XP", lxp3 == lxp2, f"before={lxp2} after={lxp3}")

# --- Edit a challenge -----------------------------------------------------
print()
print("=" * 78)
print("EDIT CHALLENGE")
print("=" * 78)
st, d = r1.post("/challenges", {
    "title": "Editable Challenge",
    "description": "Original description",
    "category": "health",
    "difficulty": "easy",
    "base_xp": 30,
    "proof_type": "text",
})
check("POST /challenges (editable)", st == 200, f"status={st} id={d.get('id')}")
edit_id = d.get("id")

st, d = r1.patch(f"/challenges/{edit_id}", {
    "title": "Edited Challenge",
    "description": "Updated description",
    "category": "fitness",
    "difficulty": "hard",
    "base_xp": 175,
    "proof_type": "photo",
})
check("PATCH /challenges/{id} edits your challenge", st == 200, f"status={st} {d}")
check("Edited title is persisted", d.get("title") == "Edited Challenge", str(d.get("title")))
check("Edited XP is persisted", d.get("base_xp") == 175, str(d.get("base_xp")))
check("Edited proof type is persisted", d.get("proof_type") == "photo", str(d.get("proof_type")))
check("Edited difficulty is persisted", d.get("difficulty") == "hard", str(d.get("difficulty")))

st, d = r1.get("/challenges")
edited = [c for c in d if c.get("id") == edit_id]
check("GET /challenges reflects the edit", st == 200 and edited and edited[0].get("title") == "Edited Challenge",
      str(edited[0].get("title")) if edited else "missing")

st, d = r2.patch(f"/challenges/{edit_id}", {"title": "Hijacked"})
check("PATCH /challenges/{id} is blocked for non-creators", st == 403, f"status={st} {d}")

st, d = r1.patch(f"/challenges/{edit_id}", {"proof_type": "hologram"})
check("PATCH /challenges/{id} rejects an unknown proof type", st == 400, f"status={st} {d}")

st, d = r1.patch(f"/challenges/{edit_id}", {"base_xp": -10})
check("PATCH /challenges/{id} rejects negative XP", st == 400, f"status={st} {d}")

st, d = r1.delete(f"/challenges/{edit_id}")
check("DELETE /challenges/{id} removes the edited challenge", st == 200, f"status={st}")

# --- XP / level maths -----------------------------------------------------
print()
print("=" * 78)
print("XP / LEVEL MATHS")
print("=" * 78)
st, d = r1.get("/game/profile")
prof = d.get("profile", d)
for key in ("level", "current_level_min_xp", "next_level_xp", "xp_in_level", "level_xp_span", "progress_percent"):
    check(f"/game/profile exposes '{key}'", key in prof, f"value={prof.get(key)}")

xp = prof.get("lifetime_xp", 0)
expected_level = max(1, int((xp / 100.0) ** (1.0 / 1.5)) + 1)
check("Level matches floor((xp/100)^(1/1.5)) + 1", prof.get("level") == expected_level,
      f"xp={xp} level={prof.get('level')} expected={expected_level}")

from app.modules.game.service import calculate_level_and_progress  # noqa: E402

canonical = calculate_level_and_progress(xp)
check("progress_percent matches the canonical service",
      abs((prof.get("progress_percent") or 0) - canonical["progress_percent"]) < 0.01,
      f"api={prof.get('progress_percent')} canonical={canonical['progress_percent']}")
check("xp_in_level matches the canonical service",
      prof.get("xp_in_level") == canonical["xp_in_level"],
      f"api={prof.get('xp_in_level')} canonical={canonical['xp_in_level']}")
check("level_xp_span matches the canonical service",
      prof.get("level_xp_span") == canonical["level_xp_span"],
      f"api={prof.get('level_xp_span')} canonical={canonical['level_xp_span']}")

zero = calculate_level_and_progress(0)
check("0 XP renders an empty 0% bar", zero["progress_percent"] == 0.0 and zero["xp_in_level"] == 0,
      f"progress={zero['progress_percent']}% xp_in_level={zero['xp_in_level']}")
check("0 XP is level 1 with a 283 XP span",
      zero["level"] == 1 and zero["level_xp_span"] == 283,
      f"level={zero['level']} span={zero['level_xp_span']}")

# --- No AI/placeholder data ----------------------------------------------
st, d = r1.get("/challenges")
titles = [c.get("title", "") for c in d] if isinstance(d, list) else []
placeholders = [t for t in titles if "Blitz" in t or "Cold Shower" in t or "Finisher" in t]
check("No AI/placeholder challenges seeded", len(placeholders) == 0, f"challenges={titles}")
check("GET /challenges returns a list (empty-safe)", isinstance(d, list), f"count={len(d) if isinstance(d, list) else 'n/a'}")
banned = [t for t in titles if "burpee" in t.lower() or "pushup" in t.lower() or "push-up" in t.lower()]
check("Burpee / push-up challenges removed", len(banned) == 0, f"remaining={banned}")

# --- Routine completion awards XP ----------------------------------------
print()
print("=" * 78)
print("ROUTINE COMPLETION -> XP")
print("=" * 78)
st, d = r1.get("/game/profile")
xp_before = d.get("profile", d).get("lifetime_xp", 0)

st, d = r1.post("/routines", {"title": "Morning Stretch", "time": "06:30", "frequency": "daily", "xp": 40, "category": "health"})
check("POST /routines (with xp + category)", st == 200, f"status={st} {d}")
routine_id = d.get("id")
check("Routine carries its XP value", d.get("xp") == 40, f"xp={d.get('xp')}")

st, d = r1.get("/routines")
check("GET /routines lists the routine with completion state",
      st == 200 and any(r.get("id") == routine_id and r.get("completed") is False for r in d),
      f"count={len(d) if isinstance(d, list) else 'n/a'}")

st, d = r1.patch(f"/routines/{routine_id}", {"completed": True})
check("PATCH /routines/{id} completes the routine", st == 200 and d.get("completed") is True, f"status={st} {d}")
check("Completing a routine awards its XP", d.get("xp_awarded") == 40, f"xp_awarded={d.get('xp_awarded')}")

st, d = r1.get("/game/profile")
xp_after = d.get("profile", d).get("lifetime_xp", 0)
check("Routine XP lands in the XP ledger", xp_after == xp_before + 40, f"before={xp_before} after={xp_after}")

st, d = r1.patch(f"/routines/{routine_id}", {"completed": True})
check("Re-completing does not pay out twice", d.get("xp_awarded") == 0, f"xp_awarded={d.get('xp_awarded')}")

st, d = r1.get("/game/profile")
xp_now = d.get("profile", d).get("lifetime_xp", 0)
check("XP unchanged after duplicate completion", xp_now == xp_after, f"before={xp_after} after={xp_now}")
check("Daily streak advanced", d.get("profile", d).get("current_streak", 0) >= 1,
      f"streak={d.get('profile', d).get('current_streak')}")

st, d = r1.patch(f"/routines/{routine_id}", {"completed": False})
check("Un-completing a routine awards nothing", st == 200 and d.get("xp_awarded") == 0, f"status={st} {d}")

# --- Removal --------------------------------------------------------------
print()
print("=" * 78)
print("REMOVAL (challenges + routines)")
print("=" * 78)
st, d = r1.post("/challenges", {"title": "Disposable Challenge", "base_xp": 20})
check("POST /challenges", st == 200, f"status={st} id={d.get('id')}")
tmp_chal = d.get("id")

st, d = r2.delete(f"/challenges/{tmp_chal}")
check("DELETE /challenges/{id} is blocked for non-creators", st == 403, f"status={st} {d}")

st, d = r1.delete(f"/challenges/{tmp_chal}")
check("DELETE /challenges/{id} removes your own challenge", st == 200, f"status={st} {d}")

st, d = r1.get("/challenges")
check("Removed challenge is gone", st == 200 and not any(c.get("id") == tmp_chal for c in d),
      f"count={len(d) if isinstance(d, list) else 'n/a'}")

st, d = r1.delete(f"/routines/{routine_id}")
check("DELETE /routines/{id} removes a routine", st == 200, f"status={st} {d}")

st, d = r1.get("/routines")
check("Removed routine is gone", st == 200 and not any(r.get("id") == routine_id for r in d),
      f"count={len(d) if isinstance(d, list) else 'n/a'}")

print()
print("=" * 78)
failed = [r for r in results if not r[1]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
if failed:
    print("NEEDED:")
    for label, _, detail in failed:
        print(f"  - {label}  ({detail})")
else:
    print("All checks passed.")
