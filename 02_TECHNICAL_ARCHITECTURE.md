# REAL-LIFE RIVALS

## Technical Architecture & Technology Stack

**Version:** 1.0\
**Architecture:** Modular Monolith\
**Deployment:** Production Web Application\
**Frontend:** React + TypeScript\
**Backend:** FastAPI + Python

## 1. Architecture Principles

-   Secure by default.
-   Modular and maintainable.
-   Scalable without unnecessary microservices.
-   API-driven and database-backed.
-   Responsive across devices.
-   Suitable for real-time multiplayer interactions.
-   Easy to test and deploy.

Start with a modular monolith. Do not introduce microservices for the
initial friend-group product.

## 2. Recommended Technology Stack

### Frontend

  Technology        Purpose
  ----------------- -------------------------------
  React             UI development
  Vite              Frontend build tooling
  TypeScript        Type safety
  Tailwind CSS      Styling
  Framer Motion     Animations
  React Router      Navigation
  TanStack Query    API state and caching
  React Hook Form   Forms
  Zod               Client-side schema validation
  Lucide Icons      Interface icons

### Backend

  Technology       Purpose
  ---------------- -------------------------------------
  Python           Backend language
  FastAPI          REST APIs
  Pydantic         Request validation
  SQLAlchemy 2.x   ORM
  Alembic          Database migrations
  PostgreSQL       Primary database
  Redis            Caching and background coordination
  WebSockets       Real-time communication
  Argon2id         Password hashing
  Pytest           Automated testing

### Storage and Infrastructure

  Technology                     Purpose
  ------------------------------ -------------------------
  S3-compatible object storage   Proof images and media
  Docker                         Containerization
  Docker Compose                 Local development
  GitHub                         Version control
  GitHub Actions                 CI/CD
  HTTPS                          Encrypted communication
  Sentry or equivalent           Error monitoring
  Structured application logs    Production diagnostics

### AI

Use an LLM API through the backend for: - Personalized task
generation. - Group challenge generation. - Difficulty
recommendations. - Challenge description generation. -
Suspicious-submission flag suggestions.

AI-generated output must be validated using Pydantic schemas before
entering the challenge workflow.

## 3. High-Level Architecture

``` text
                    USERS
                      |
                      v
              FRONTEND APPLICATION
             React + TypeScript + Vite
                      |
                HTTPS / WSS
                      |
                      v
                FASTAPI BACKEND
                      |
      +---------------+----------------+
      |               |                |
      v               v                v
 AUTH MODULE    CHALLENGE MODULE    GAME MODULE
      |               |                |
      +---------------+----------------+
                      |
              SERVICE LAYER
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
  PostgreSQL        Redis        Object Storage
       |
       v
  Persistent Data

       Backend Services
              |
              v
          AI Provider
```

## 4. Backend Module Responsibilities

-   **Authentication:** Registration, login, email verification,
    password reset, session management, token rotation.
-   **User:** Profile management, avatar selection, preferences,
    statistics.
-   **Group:** Group creation, invitations, membership, permissions.
-   **Challenge:** Challenge creation, assignment, deadlines, lifecycle.
-   **Submission:** Proof uploads, verification, approval, rejection,
    disputes.
-   **Game:** XP transactions, levels, streaks, achievements,
    leaderboard, race positions.
-   **AI:** Prompt construction, structured response validation,
    challenge suggestions, usage limits.
-   **Notification:** In-app notifications, email notifications,
    WebSocket events.

## 5. Authentication Architecture

Login is mandatory for all application functionality.

Public routes: - `/` - `/login` - `/register` - `/verify-email` -
`/forgot-password` - `/reset-password`

Protected routes: - `/dashboard` - `/groups` - `/challenges` - `/race` -
`/leaderboard` - `/profile` - `/admin`

### Authentication flow

1.  User registers.
2.  Backend validates email and password.
3.  Password is hashed using Argon2id.
4.  Verification email is sent.
5.  User verifies the email.
6.  User logs in.
7.  Backend establishes an authenticated session.
8.  User accesses protected resources.
9.  Expired sessions are refreshed securely.
10. Logout revokes the session.

### Session implementation

-   Short-lived access token.
-   Rotating refresh token.
-   Secure, HttpOnly, SameSite cookies.
-   Server-side refresh-session records.
-   CSRF protection for cookie-authenticated state-changing requests.
-   Refresh-token reuse detection and session revocation.

Never store passwords or long-lived authentication tokens in browser
localStorage.

## 6. Real-Time Architecture

Use WebSockets for: - Live race updates. - Leaderboard changes. - New
challenge announcements. - Submission notifications. - Friend activity.

Every WebSocket connection must authenticate the user, check group
membership, restrict subscriptions to authorized groups, validate
incoming events, and reconnect/synchronize using persisted server state.

Redis can support cross-process message distribution when multiple
backend instances are deployed.

## 7. Background Processing

Use a background task system for: - Sending emails. - Processing
uploaded media. - Scheduled challenge expiration. - Streak
calculations. - Season closure. - Notifications. - AI challenge
generation.

A lightweight job worker with Redis-backed scheduling is suitable when
tasks grow beyond FastAPI's simple background tasks.

## 8. Deployment Architecture

  Component    Hosting requirement
  ------------ ---------------------------------------
  Frontend     Static hosting with HTTPS
  Backend      Persistent Python application hosting
  Database     Managed PostgreSQL
  Media        Private object storage
  Redis        Managed Redis when needed
  Domain       Custom domain
  Monitoring   Error tracking and uptime monitoring

Potential choices include Vercel or Cloudflare Pages for frontend
hosting, and Render, Railway, or another managed container platform for
FastAPI. Select providers based on region, pricing, persistent storage,
backups, outbound email, WebSocket support, and deployment requirements.

## 9. Environment Configuration

Maintain separate development, staging, and production environments.

Example `.env.example`:

``` env
APP_ENV=development
APP_NAME=RealLifeRivals

DATABASE_URL=
REDIS_URL=

JWT_SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

FRONTEND_URL=
BACKEND_URL=

EMAIL_HOST=
EMAIL_PORT=
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_FROM=

OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_BUCKET=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=

AI_API_KEY=
```

Never commit real secrets. Production secrets must be configured through
the hosting provider's secret-management facilities.

## 10. Scalability Strategy

### Initial release

-   One FastAPI application.
-   Managed PostgreSQL.
-   Object storage.
-   Single background worker if required.

### Growth stage

-   Multiple API instances.
-   Redis-backed WebSocket distribution.
-   Database connection pooling.
-   Background job workers.
-   CDN for public assets.
-   Query optimization.

### Larger scale

-   Separate resource-intensive workloads.
-   Read replicas where justified.
-   Dedicated media processing.
-   More sophisticated event processing.

Do not optimize for millions of users before the initial friend-group
product is validated.

## 11. Architecture Acceptance Criteria

-   Frontend and backend operate independently.
-   All application data persists in PostgreSQL.
-   Authentication works across page refreshes.
-   WebSocket connections are authenticated.
-   File uploads use private storage.
-   Secrets are never exposed to the frontend.
-   Database migrations are repeatable.
-   Staging and production configurations are separate.
-   Deployment can be reproduced using documented instructions.
