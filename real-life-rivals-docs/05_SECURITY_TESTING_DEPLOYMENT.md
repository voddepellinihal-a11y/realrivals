# REAL-LIFE RIVALS

## Security, Testing & Production Deployment Plan

**Version:** 1.0\
**Environment:** Public Internet\
**Authentication:** Mandatory for application access\
**Release:** Production MVP

## 1. Production Security Objectives

Protect: - User accounts. - Passwords and sessions. - Private group
information. - Competition records. - Uploaded proof images. - User
activity. - XP and leaderboard integrity. - Administrative operations.

Security must be implemented before public launch, not added as a later
enhancement.

## 2. Authentication Security

### Registration

-   Validate email format.
-   Enforce username uniqueness.
-   Enforce password requirements.
-   Hash passwords with Argon2id.
-   Require email verification.
-   Rate-limit registration.
-   Prevent automated account creation where necessary.

### Login

-   Validate credentials on the backend.
-   Return generic errors to avoid account enumeration.
-   Rate-limit failed login attempts.
-   Establish a secure authenticated session.
-   Record security-relevant login events.
-   Provide session revocation.

### Session Management

-   Short-lived access credentials.
-   Refresh-token rotation.
-   HttpOnly, Secure, and SameSite cookies.
-   CSRF protection.
-   Server-side session records.
-   Logout and revoke sessions.
-   Detect refresh-token reuse.

### Password Recovery

-   Secure single-use reset tokens.
-   Store token hashes.
-   Apply token expiry.
-   Invalidate the token after use.
-   Avoid exposing whether an email is registered.

## 3. Authorization

Use role-based and resource-based authorization.

Roles: - `USER` - `GROUP_ADMIN` - `PLATFORM_ADMIN`

Rules: - A user can access only their own account settings. - A group
member can access only authorized group resources. - Group
administrators can manage only their groups. - Users cannot approve
their own submissions. - Platform administrator privileges must be
restricted. - Every sensitive backend operation checks authorization.

Never rely on hiding buttons or pages in React as a security measure.

## 4. File Upload Security

Supported MVP formats: - JPEG. - PNG. - WebP.

Requirements: - Maximum upload size configurable, initially 10 MB. -
Validate actual file content, not just filename extensions. - Generate
server-controlled object keys. - Reject executable and unsupported
content. - Use private object storage. - Use signed URLs with limited
expiry. - Prevent public access to private evidence. - Apply malware
scanning where appropriate. - Limit uploads per user and assignment.

Videos can be added after establishing appropriate storage and
processing limits.

## 5. Application Security

Implement: - HTTPS everywhere. - Secure HTTP headers. - CORS
allowlist. - CSRF protection where applicable. - SQL injection
prevention through parameterized ORM queries. - Input validation. -
Output encoding. - Rate limiting. - Secure secret management. -
Dependency vulnerability scanning. - Audit logging. - Request-size
limits.

Do not expose stack traces, internal file paths, or secrets in
production error responses.

## 6. Game Integrity

The frontend must never determine authoritative: - XP awards. - Final
scores. - Streak counts. - Race positions. - Achievement unlocks. -
Season results.

The backend calculates and validates these values.

Implement: - Idempotent XP awards. - Database transaction protection. -
Duplicate submission prevention. - Approval authorization. - Audit logs
for adjustments. - Challenge deadline enforcement. - Season finalization
safeguards.

AI must never directly approve a task or write XP transactions.

## 7. Privacy Requirements

-   Publish a privacy policy.
-   Publish terms of service.
-   Explain what evidence is collected.
-   Obtain permission before requesting location.
-   Do not collect continuous background GPS.
-   Keep proof images private.
-   Provide account deletion.
-   Provide a data retention policy.
-   Limit personal information displayed to group members.
-   Provide notification preferences.

Design for applicable Indian data-protection requirements, including the
Digital Personal Data Protection Act and applicable rules and
commencement provisions. Obtain appropriate legal review before public
launch.

## 8. Testing Strategy

### A. Unit Testing

Backend: - Authentication utilities. - XP calculations. - Streak
calculations. - Race position calculations. - Challenge validation. -
Permission checks.

Frontend: - Form validation. - Challenge components. - Progress
indicators. - Protected route behavior. - Error and loading states.

### B. Integration Testing

Test: - Registration and email verification. - Login and logout. - Token
refresh and session revocation. - Group creation and membership. -
Challenge assignment. - Proof upload. - Submission review. - XP
awarding. - Streak updates. - Leaderboard calculation. - Season
finalization.

### C. End-to-End Testing

Use Playwright for important user journeys.

**Journey 1** 1. Register. 2. Verify email. 3. Log in. 4. Complete
onboarding. 5. Create a group.

**Journey 2** 1. Register another user. 2. Join the first user's group.
3. Receive a challenge. 4. Submit proof. 5. Get approval. 6. Verify XP
and streak updates.

**Journey 3** 1. Connect multiple users. 2. Approve different tasks. 3.
Observe race updates. 4. Refresh the browser. 5. Verify persisted race
positions.

**Journey 4** 1. Submit a task. 2. Attempt duplicate approval. 3. Verify
only one XP transaction exists.

### D. Security Testing

Test: - Unauthorized API requests. - Invalid tokens. - Expired
sessions. - Cross-group access. - Self-approval. - Duplicate XP. -
Malicious file uploads. - Rate-limit enforcement. - WebSocket
authentication. - Session revocation. - Password-reset abuse.

### E. Performance Testing

Use Locust or an equivalent tool.

Initial testing targets: - 50 concurrent authenticated users. - 100
simultaneous API requests under load testing. - 20 concurrent WebSocket
connections. - No duplicate XP during concurrent approvals. - No
cross-group information leakage. - No critical errors during race
updates.

These are initial engineering targets, not guarantees of production
capacity.

## 9. CI/CD Pipeline

Use GitHub Actions.

Pipeline: 1. Checkout repository. 2. Install dependencies. 3. Run
formatting checks. 4. Run frontend linting. 5. Run TypeScript checks. 6.
Run frontend tests. 7. Run backend linting. 8. Run backend unit tests.
9. Run integration tests. 10. Build frontend. 11. Build backend
container. 12. Run dependency and security scans. 13. Deploy to staging.
14. Run staging smoke tests. 15. Approve production deployment. 16.
Deploy production. 17. Verify health checks.

Production deployments must not proceed when required checks fail.

Database migrations must have a documented recovery plan.

## 10. Deployment Environments

### Development

-   Local frontend.
-   Local FastAPI.
-   Local PostgreSQL.
-   Test email service.
-   Development storage.

### Staging

-   Separate database.
-   Separate storage bucket.
-   Test domain.
-   Production-like configuration.
-   Automated integration tests.

### Production

-   Custom domain.
-   HTTPS.
-   Managed PostgreSQL.
-   Private object storage.
-   Production email provider.
-   Secret management.
-   Backups.
-   Monitoring.
-   Error alerts.

Never use production user data as unrestricted test data.

## 11. Suggested Production Domains

Example: - `yourdomain.com` --- public landing page. -
`app.yourdomain.com` --- authenticated application. -
`api.yourdomain.com` --- backend APIs.

Use one consistent authentication and cookie strategy across the chosen
domains.

## 12. Monitoring and Maintenance

Monitor: - Backend availability. - API response times. - Database
availability. - Database connection usage. - WebSocket failures. -
Failed login rates. - Email delivery. - File upload errors. - Background
job failures. - XP calculation anomalies.

Maintain: - Automated database backups. - Periodic restore tests. -
Dependency updates. - Security patches. - Error logs. - Deployment
history. - Incident response procedures.

Suggested initial operational targets: - 99.5% monthly availability. -
Automated daily database backups. - Documented recovery procedures. -
Alerts for critical application failures.

## 13. Launch Checklist

### Authentication

-   [ ] Registration works.
-   [ ] Email verification works.
-   [ ] Login works.
-   [ ] Logout works.
-   [ ] Password reset works.
-   [ ] Session expiration works.
-   [ ] Session revocation works.
-   [ ] All private application routes require login.

### Application

-   [ ] Groups work.
-   [ ] Invitations work.
-   [ ] Challenges work.
-   [ ] Submissions work.
-   [ ] Verification works.
-   [ ] XP is accurate.
-   [ ] Streaks work.
-   [ ] Leaderboard works.
-   [ ] Multiplayer race works.
-   [ ] New Year season works.

### Security

-   [ ] HTTPS enabled.
-   [ ] Secrets protected.
-   [ ] Private storage enabled.
-   [ ] Authorization tested.
-   [ ] Rate limiting enabled.
-   [ ] Audit logging enabled.
-   [ ] Privacy policy published.
-   [ ] Terms published.
-   [ ] Account deletion tested.

### Deployment

-   [ ] Production frontend deployed.
-   [ ] Production backend deployed.
-   [ ] Database migrations completed.
-   [ ] Email delivery configured.
-   [ ] Storage configured.
-   [ ] Backups configured.
-   [ ] Monitoring configured.
-   [ ] Domain configured.
-   [ ] Smoke tests passed.

## 14. Production Release Criteria

The application may be publicly launched only when: 1. All critical
authentication workflows work. 2. Unauthorized users cannot access
protected data. 3. Group-level data isolation is verified. 4. XP and
race calculations are server-controlled. 5. Core end-to-end tests pass.
6. Critical security issues are resolved. 7. Production database backups
are operational. 8. Email verification and password recovery are
operational. 9. Monitoring and incident procedures exist. 10. Privacy
and legal requirements have been reviewed.

**Final rule:** A visually complete application is not a
production-ready application. Security, persistence, authorization,
testing, and operational recovery are mandatory release requirements.
