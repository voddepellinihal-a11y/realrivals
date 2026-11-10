# Implementation Plan: Real-Life Rivals

## Overview

Real-Life Rivals is a multiplayer real-world challenge platform. Users form private
groups, take turns participating in shared/personal daily challenges, submit photo
proof, earn XP, maintain streaks, unlock achievements, and race together on a shared
virtual track.

The MVP acceptance criteria (from `01_PRD.md`): a user can register, verify an email,
log in, create or join a group, receive challenges, submit evidence, obtain verification,
earn XP, maintain a streak, and see their avatar move on the shared race track. All
competition data must persist after logout, refresh, and deployment restarts.

This plan decomposes the five source specs (`01_PRD.md` … `05_SECURITY_TESTING_DEPLOYMENT.md`,
indexed by `README.md`) into small, verifiable tasks. Implementation starts from an empty
codebase; the docs are the initial specification. Conflicts or ambiguities must be documented
and resolved before coding.

## Architecture Decisions

- **Modular monolith** (FastAPI backend + React frontend) — explicit product constraint;
  no microservices for MVP.
- **Backend modules:** auth, user, group, challenge, submission, game, notification, ai,
  admin — aligned with module responsibilities in the architecture spec.
- **Frontend:** React + TypeScript + Vite, Tailwind CSS, TanStack Query, React Hook Form,
  Zod; API base `/api/v1`; auth via HttpOnly cookies with refresh-token rotation.
- **Data:** PostgreSQL (SQLAlchemy 2 + Alembic), Redis (cache/pubsub), S3-compatible private
  object storage for proof media, FastAPI background tasks (move to worker when tasks grow).
- **Scoring:** server-authoritative; immutable, idempotent XP transactions; streaks use
  configured group/user timezone; race positions are cached projections over authoritative XP.
- **Real-time:** WebSockets for `race.position_updated`, `leaderboard.updated`, submission and
  notification events; publish only after successful DB commit; Redis pub/sub when scaled.
- **AI:** LLM via backend for challenge suggestions; all AI output validated via Pydantic
  before entering the challenge workflow; authorized publication required.

## Task List

### Phase 1: Foundation

- [x] **Task 1: Scaffold monorepo, local dev environment, CI skeleton**
  - **Description:** Create the initial repository layout (`backend/`, `frontend/`, `docker-compose.yml`,
    `.github/workflows/`, `.env.example`) with a FastAPI app factory + module skeleton, a React+Vite
    TypeScript app, Docker Compose (api, postgres, redis, frontend), and a CI workflow skeleton.
  - **Acceptance criteria:**
    - [ ] Repo contains `backend/` and `frontend/` with runnable entrypoints.
    - [ ] `docker-compose.yml` defines backend, PostgreSQL, Redis (and frontend service).
    - [ ] `.env.example` documents required environment variables.
    - [ ] CI workflow skeleton passes on an empty build.
  - **Verification:**
    - [ ] `docker compose config` is valid.
    - [ ] Backend imports/starts locally; frontend production build succeeds.
    - [ ] CI workflow parses.
  - **Dependencies:** None
  - **Files likely touched:** `docker-compose.yml`, `backend/app/main.py`, `backend/app/core/`, `frontend/`, `.github/workflows/ci.yml`, `.env.example`
  - **Estimated scope:** Medium (3-5 files)

- [x] **Task 2: Database schema + Alembic baseline migrations (auth, user, profile, gamification tables)**
  - **Description:** Baseline schema for USERS, USER_PREFERENCES, AVATARS, ACHIEVEMENTS, USER_ACHIEVEMENTS,
    XP_TRANSACTIONS, STREAKS, AUTH_SESSIONS, EMAIL_VERIFICATION_TOKENS, PASSWORD_RESET_TOKENS with UUID PKs,
    FKs, and key unique constraints; versioned via Alembic.
  - **Acceptance criteria:**
    - [ ] Migration creates the listed tables with correct column types and constraints.
    - [ ] `alembic upgrade head` succeeds against PostgreSQL; `alembic downgrade base` succeeds.
  - **Verification:**
    - [ ] Upgrade/downgrade run cleanly against Postgres (Docker).
  - **Dependencies:** Task 1
  - **Files likely touched:** `backend/alembic/versions/`, `backend/app/models/`
  - **Estimated scope:** Medium (3-5 files)

- [x] **Task 3: Auth backend module — registration, login, logout, refresh, sessions**
  - **Description:** FastAPI auth module: register/login/logout/refresh endpoints, Argon2id password hashing,
    short-lived access + rotating refresh tokens (HttpOnly cookies, server-side session records, revocation).
  - **Acceptance criteria:**
    - [ ] Registration hashes password with Argon2id; login validates; logout revokes session.
    - [ ] Refresh token rotates; reuse detection/revocation works.
    - [ ] Protected dependency enforces authentication.
  - **Verification:**
    - [ ] Auth module tests pass (register/login/refresh/logout).
  - **Dependencies:** Task 2
  - **Files likely touched:** `backend/app/modules/auth/`, `backend/tests/`
  - **Estimated scope:** Medium (3-5 files)

- [ ] **Task 4: Auth frontend — screens, protected routes, API client**
  - **Description:** Register, login, email-verification, forgot/reset-password screens; protected route guard;
    API client configured for cookie credentials.
  - **Acceptance criteria:**
    - [ ] Public routes (`/`, `/login`, `/register`, `/verify-email`, `/forgot-password`, `/reset-password`)
      and protected routes (`/dashboard`, ...) enforced per spec.
  - **Verification:**
    - [ ] Frontend builds; auth screens render; protected routes guard correctly.
  - **Dependencies:** Task 3
  - **Files likely touched:** `frontend/src/`
  - **Estimated scope:** Medium (3-5 files)

### Checkpoint: Foundation
- [ ] All foundation tasks verified (auth backend + frontend wired).
- [ ] All tests pass; builds clean.
- [ ] Review with human before proceeding.

### Phase 2: Core Competition Loop

- [ ] **Task 5: Groups backend — create/join via invite code, membership, admin**
  - **Description:** Group creation, join via invite code/link, member management, admin role assignment,
    group data isolation.
  - **Acceptance criteria:**
    - [ ] Private groups created; join via code works; only authorized members access group data.
  - **Verification:** Group module tests; cross-group isolation checks.
  - **Dependencies:** Task 4
  - **Files likely touched:** `backend/app/modules/group/`
  - **Estimated scope:** Medium (3-5 files)

- [ ] **Task 6: Challenges backend — CRUD, publish, assignments**
  - **Description:** Challenge creation (admin/friend sources), publish, assignment to group members
    (common challenge = per-member assignments; personal challenges), daily challenge retrieval.
  - **Acceptance criteria:**
    - [ ] Challenge lifecycle (draft → published) enforced; assignments valid.
  - **Verification:** Challenge module tests.
  - **Dependencies:** Task 5
  - **Files likely touched:** `backend/app/modules/challenge/`
  - **Estimated scope:** Medium (3-5 files)

- [ ] **Task 7: Submissions backend — presigned upload + proof submission**
  - **Description:** Presigned upload URL issuance to private object storage; submission creation tied to
    assignment with attempt limits and proof metadata.
  - **Acceptance criteria:**
    - [ ] Client can obtain upload URL and submit photo proof scoped to an assignment.
  - **Verification:** Submission module tests (upload flow, validation).
  - **Dependencies:** Task 6
  - **Files likely touched:** `backend/app/modules/submission/`
  - **Estimated scope:** Small (1-2 files)

- [ ] **Task 8: Submissions backend — review workflow + idempotent XP award + streak update**
  - **Description:** Friend/admin review of submissions; self-review forbidden; approve/reject; approval
    triggers server-authoritative, idempotent XP award and streak qualification.
  - **Acceptance criteria:**
    - [ ] Only authorized reviewers review; approval awards XP exactly once (idempotency).
  - **Verification:** Submission/game tests for duplicate-award prevention.
  - **Dependencies:** Task 7
  - **Files likely touched:** `backend/app/modules/submission/`, `backend/app/modules/game/`
  - **Estimated scope:** Medium (3-5 files)

### Checkpoint: Core Competition Loop
- [ ] End-to-end MVP path verified: group → challenge → submission → approval → XP.
- [ ] All tests pass; builds clean.
- [ ] Review with human before proceeding.

### Phase 3: Gamification & Race

- [ ] **Task 9: Game backend — XP, levels, streaks, achievements, leaderboard, race positions**
  - **Description:** XP transaction/leveling, streaks, achievements, season leaderboard, race position
    projection; server-authoritative writes, cached race projection.
  - **Acceptance criteria:**
    - [ ] XP/streaks/race data consistent; leaderboard reflects authoritative XP.
  - **Verification:** Game module tests; scoring consistency tests.
  - **Dependencies:** Task 8
  - **Files likely touched:** `backend/app/modules/game/`
  - **Estimated scope:** Medium (3-5 files)

- [ ] **Task 10: Race + real-time — WebSocket events**
  - **Description:** Authenticated WebSocket connections scoped to authorized groups; publish
    `race.position_updated`, `leaderboard.updated`, submission events, notifications after commit.
  - **Acceptance criteria:**
    - [ ] WS events authenticate user, check group membership, validate payloads.
  - **Verification:** WebSocket integration tests.
  - **Dependencies:** Task 9
  - **Files likely touched:** `backend/app/modules/realtime/` (or within game)
  - **Estimated scope:** Medium (3-5 files)

### Phase 4: AI, Admin, Notifications, Launch Readiness

- [ ] **Task 11: AI challenge generation — LLM suggestions + Pydantic validation + authorized publish**
  - **Description:** Backend LLM integration for personalized/group challenge suggestions; structured
    output validated via Pydantic; AI cannot publish directly — authorized publication required.
  - **Acceptance criteria:**
    - [ ] AI output validates; publication requires authorization.
  - **Verification:** AI module tests (validation, gating).
  - **Dependencies:** Task 6
  - **Files likely touched:** `backend/app/modules/ai/`
  - **Estimated scope:** Small (1-2 files)

- [ ] **Task 12: Notifications — in-app + WebSocket + email triggers**
  - **Description:** Notification records and delivery (in-app, WebSocket, email) for challenge publish,
    submission review, streak reminders, invites, leaderboard changes, season events.
  - **Acceptance criteria:**
    - [ ] Events trigger notifications without blocking core flows.
  - **Verification:** Notification module tests.
  - **Dependencies:** Tasks 8, 10
  - **Files likely touched:** `backend/app/modules/notification/`
  - **Estimated scope:** Small (1-2 files)

- [ ] **Task 13: Admin dashboard backend + frontend**
  - **Description:** Admin endpoints for group/challenge/submission/season management and dispute resolution;
    admin frontend screens.
  - **Acceptance criteria:**
    - [ ] Admin can manage groups, publish/assign challenges, review disputes, configure seasons.
  - **Verification:** Admin module tests; frontend admin screens build.
  - **Dependencies:** Tasks 5, 6, 8
  - **Files likely touched:** `backend/app/modules/admin/`, `frontend/src/`
  - **Estimated scope:** Medium (3-5 files)

- [ ] **Task 14: Testing, security hardening, CI/CD, deployment, launch checklist**
  - **Description:** Expand automated tests per security/testing spec; security hardening pass (auth,
    validation, storage, headers); CI/CD pipeline; deployment; launch checklist sign-off.
  - **Acceptance criteria:**
    - [ ] Security checklist items implemented; launch checklist completed.
  - **Verification:** Full test suite; security review; CI green; deployment reproducible.
  - **Dependencies:** Tasks 1–13
  - **Files likely touched:** `backend/tests/`, `frontend/`, `.github/workflows/`, `docs/`
  - **Estimated scope:** Medium (3-5 files)

### Checkpoint: MVP Complete
- [ ] All MVP acceptance criteria met (PRD §11).
- [ ] All tests pass; builds clean; security/deployment checks complete.
- [ ] Ready for human review before shipping.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auth/session complexity (rotation, CSRF, reuse detection) | High | Task-level auth tests; incremental hardening in Task 14 |
| XP duplicate-award / race consistency | High | Idempotency keys + DB constraints; transactional scoring |
| Realtime fan-out consistency | Medium | Publish after commit; Redis pub/sub at scale |
| AI output invalid/prompt risk | Medium | Strict Pydantic validation + authorization gates (Task 11) |
| Scope creep beyond MVP | High | Stick to MVP scope; AI gen deferred until core engine stable (PRD §7) |

## Open Questions

- Provider selection for email (SMTP), LLM, object storage, hosting (frontend/backend/DB/Redis).
- Avatar asset source and unlock-level rules.
- Season scoping details (group vs user leaderboard) — spec says season-based.
