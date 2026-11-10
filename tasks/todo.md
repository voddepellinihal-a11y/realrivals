# Task List: Real-Life Rivals

> Status as of 2026-11-10. Server: `http://127.0.0.1:8000` (FastAPI + Supabase Postgres via the
> connection pooler). Frontend is a Vite/React build served from `frontend/dist`.

## Phase 1: Foundation

- [x] Task 1: Scaffold monorepo, local dev environment, CI skeleton
- [x] Task 2: Database schema + Alembic baseline migrations (auth, user, profile, gamification tables)
- [x] Task 3: Auth backend module — registration, login, logout, refresh, sessions
- [x] Task 4: Auth frontend — screens, protected routes, API client

### Checkpoint: Foundation
- [x] All foundation tasks verified (auth backend + frontend wired)
- [x] All tests pass; builds clean
- [ ] Review with human before proceeding

## Phase 2: Core Competition Loop

- [x] Task 5: Groups backend — create/join via invite code, membership, admin
- [x] Task 6: Challenges backend — CRUD, publish, assignments, **edit**, **remove**, direct 1v1
- [x] Task 7: Submissions backend — photo (base64) / text / link proof submission
- [x] Task 8: Submissions backend — review workflow + idempotent XP award + streak update

### Checkpoint: Core Competition Loop
- [x] End-to-end MVP path verified: challenge → submission → approval → XP
- [x] All tests pass; builds clean
- [ ] Review with human before proceeding

## Phase 3: Gamification & Race

- [x] Task 9: Game backend — XP, levels, streaks, achievements, leaderboard
  - [x] Canonical level/XP service (`app/modules/game/service.py`) — one source of truth
  - [x] 0 XP renders an empty 0% bar; level = `floor((xp/100)^(1/1.5)) + 1`
  - [x] Routine completion awards XP once per routine per day (idempotent ledger)
  - [x] XP/streak/level exposed by `/game/profile` and `/auth/me`
- [ ] Task 10: Race + real-time — WebSocket events (live race track not built)

### Checkpoint: After Phase 3
- [x] Gamification tasks verified
- [ ] Review with human before proceeding

## Phase 4: AI, Admin, Notifications, Launch Readiness

- [ ] Task 11: AI challenge generation — LLM suggestions + Pydantic validation + authorized publish
- [ ] Task 12: Notifications — in-app + WebSocket + email triggers
- [ ] Task 13: Admin dashboard backend + frontend
- [ ] Task 14: Testing, security hardening, CI/CD, deployment, launch checklist
  - [x] Unit + API test suites (`pytest`, 72 tests) and an end-to-end verification script (68 checks)
  - [x] Production-boot simulation script (`tests/verify_production_boot.py`)
  - [x] Render Blueprint (`render.yaml`) — single service, builds SPA + API, runs migrations
  - [x] `JWT_SECRET_KEY` read from the environment (Render generates it); app refuses to boot in
        production without a ≥ 32-byte secret
  - [x] SPA history fallback + CORS + static-asset caching rules
  - [x] `psycopg2-binary` added to `backend/requirements.txt` (the DB driver was missing)
  - [ ] SMTP credentials configured so verification / password-reset emails are delivered
  - [ ] Public deployment executed (Render account / repo push required)

### Deployment prep status
- [x] `render.yaml` blueprint validated against Render's Blueprint spec
- [x] Production-boot simulation passes (`tests/verify_production_boot.py`)
- [x] Alembic build failure fixed: `DATABASE_URL` is resolved from the environment and normalised
      (`postgres://` / `postgresql://` / `postgresql+psycopg://` → `postgresql+psycopg2://`), and a
      `%`-encoded password no longer breaks ConfigParser's interpolation
- [x] `python -m app.db.check_database` pre-flight runs before the migrations and reports the
      resolved host/port (password masked) with an actionable cause
- [x] Git repository initialised on `main`, working tree clean
- [x] Pushed to https://github.com/voddepellinihal-a11y/realrivals (public repo, branch `main`)
- [x] `.gitignore` / `.gitattributes` added; no `.env`, `node_modules`, `dist` or bytecode tracked
- [x] Supabase credentials scrubbed from every committed file (only `backend/.env`, which is ignored,
      still holds them locally)
- [x] Seeded account passwords moved out of the source (`RIVAL1_PASSWORD` / `RIVAL2_PASSWORD`,
      required in production) + `python -m app.db.rotate_seeded_passwords` for existing databases
- [ ] Render: create the Blueprint from the repo and set `DATABASE_URL` + the SMTP vars
- [ ] Run `python -m app.db.rotate_seeded_passwords` once with the same values set on Render
- [ ] Read the generated `RIVAL1_PASSWORD` / `RIVAL2_PASSWORD` from Render's Environment tab to log in

### Checkpoint: MVP Complete
- [ ] All MVP acceptance criteria met (PRD §11)
- [x] All tests pass; builds clean
- [ ] Ready for human review before shipping

## Design System (current)

| Role | Colour | Where |
| --- | --- | --- |
| App background | `#18181B` deep charcoal / slate | page + root containers |
| Card / modal surface | `#0F172A` midnight navy | cards, modals, elevated surfaces |
| Border (flat, no glow) | `#1E293B` | card + input outlines |
| XP progress + primary accents | `#F59E0B` vivid amber (+ `#FFFFFF` text) | XP bar, headings, badges, checkmarks |
| Action buttons + challenge highlights | `#3B82F6` deep slate blue | CTAs, versus cards, proof actions |

Semantic-only exception: destructive / error states use a muted red (`#f87171` text on
`rgba(239,68,68,.1)`) because amber is reserved for positive accents.

## Recently completed

- [x] Brand palette migrated across `App.tsx`, `Dashboard.tsx`, `VersusCard.tsx`,
      `ProofPreviewModal.tsx`, `ErrorBoundary.tsx`, `tailwind.config.js`, `index.css`
- [x] Routines now award XP (`PATCH /routines/{id}`), advance the streak, and update the bar live
- [x] Remove buttons for routines and challenges (`DELETE /routines/{id}`, `DELETE /challenges/{id}`)
- [x] Edit Challenge (`PATCH /challenges/{id}`) — title, description, category, difficulty, XP, proof type
- [x] Seeded burpee / push-up / "10 min physical activity" challenges purged from the database
- [x] Static asset caching fixed (`index.html` no-cache, hashed assets immutable) so a rebuild is picked up
      immediately instead of serving a stale bundle
- [x] Deployment readiness:
  - `render.yaml` blueprint (runtime `python`, migrations in the build command, `/health` probe)
  - `ENVIRONMENT` / `JWT_SECRET_KEY` / `CORS_ORIGINS` read from the environment; unknown vars ignored
  - `psycopg2-binary` added to `backend/requirements.txt`
  - SPA history fallback (`/login`, `/dashboard`, `/onboarding` → `index.html`, 200)
  - API paths still return JSON 404s instead of the HTML shell
  - `FRONTEND_URL` falls back to Render's `RENDER_EXTERNAL_URL` for email links
