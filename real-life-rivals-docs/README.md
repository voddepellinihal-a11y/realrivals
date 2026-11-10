# Real-Life Rivals --- Project Documentation

This folder contains the five core specification documents for the
Real-Life Rivals production web application.

## Documents

1.  [Product Requirements Document](01_PRD.md) --- product vision,
    roles, features, MVP, and acceptance criteria.
2.  [Technical Architecture & Technology
    Stack](02_TECHNICAL_ARCHITECTURE.md) --- architecture, stack,
    authentication, real-time design, deployment, and scalability.
3.  [Database Design & API
    Specification](03_DATABASE_API_SPECIFICATION.md) --- data model,
    relationships, REST endpoints, WebSocket events, and business rules.
4.  [UI/UX & Design System](04_UI_UX_DESIGN_SYSTEM.md) --- visual
    identity, routes, screens, components, animations, and responsive
    requirements.
5.  [Security, Testing & Production
    Deployment](05_SECURITY_TESTING_DEPLOYMENT.md) --- authentication
    security, authorization, privacy, tests, CI/CD, deployment, and
    launch checklist.

## Important product constraints

-   The application is intended to be deployed publicly.
-   The landing page and authentication pages may be public.
-   All competition features and private user/group data require login.
-   Email verification is required before normal application access.
-   Backend authorization is mandatory; frontend route guards alone are
    insufficient.
-   XP, streaks, achievements, race positions, and final rankings are
    server-authoritative.
-   Proof media must use private object storage.
-   Start with a modular monolith; do not introduce microservices
    prematurely.

## Development instruction

Read all five documents before implementing features. Treat them as the
initial project specification. If requirements conflict or are
ambiguous, document the conflict and resolve it before coding.

## Suggested repository structure

``` text
real-life-rivals/
├── docs/
│   ├── README.md
│   ├── 01_PRD.md
│   ├── 02_TECHNICAL_ARCHITECTURE.md
│   ├── 03_DATABASE_API_SPECIFICATION.md
│   ├── 04_UI_UX_DESIGN_SYSTEM.md
│   └── 05_SECURITY_TESTING_DEPLOYMENT.md
├── frontend/
├── backend/
├── tests/
├── .github/
├── .env.example
└── README.md
```
