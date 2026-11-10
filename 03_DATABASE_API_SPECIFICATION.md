# REAL-LIFE RIVALS

## Database Design & API Specification

**Version:** 1.0\
**Database:** PostgreSQL\
**ORM:** SQLAlchemy 2.x\
**API:** REST + WebSockets

## 1. Database Design Principles

1.  UUID primary keys.
2.  Foreign-key relationships.
3.  UTC timestamps.
4.  Database constraints for important business rules.
5.  Indexes for frequently queried fields.
6.  Transactional scoring operations.
7.  Immutable XP transaction history.
8.  Private media storage.
9.  Explicit ownership and group authorization.
10. Version-controlled Alembic migrations.

## 2. Database Tables

### USERS

  Column           Type           Description
  ---------------- -------------- ---------------------
  id               UUID           Primary key
  username         VARCHAR(30)    Unique username
  email            VARCHAR(255)   Unique email
  password_hash    TEXT           Argon2id hash
  email_verified   BOOLEAN        Verification status
  avatar_id        UUID           Selected avatar
  is_active        BOOLEAN        Account status
  created_at       TIMESTAMPTZ    Creation date
  updated_at       TIMESTAMPTZ    Last update

### USER_PREFERENCES

-   id
-   user_id
-   interests
-   timezone
-   notification_preferences
-   created_at
-   updated_at

### GROUPS

-   id
-   name
-   description
-   invite_code_hash
-   created_by
-   is_active
-   created_at

### GROUP_MEMBERS

-   id
-   group_id
-   user_id
-   role
-   status
-   joined_at

Constraint: `UNIQUE(group_id, user_id)`.

### SEASONS

-   id
-   group_id
-   name
-   start_at
-   end_at
-   status
-   scoring_rules
-   created_at

### SEASON_MEMBERS

-   id
-   season_id
-   user_id
-   starting_xp
-   final_xp
-   final_rank
-   joined_at

Constraint: `UNIQUE(season_id, user_id)`.

### CHALLENGES

-   id
-   creator_id
-   group_id
-   title
-   description
-   category
-   difficulty
-   base_xp
-   challenge_type
-   verification_method
-   source_type
-   status
-   created_at
-   published_at

`source_type` values: `ADMIN`, `FRIEND`, `AI`.

### CHALLENGE_ASSIGNMENTS

-   id
-   challenge_id
-   user_id
-   group_id
-   season_id
-   due_at
-   status
-   assigned_at
-   completed_at

A common group challenge has one assignment per participating member
while retaining one shared challenge definition.

### SUBMISSIONS

-   id
-   assignment_id
-   user_id
-   attempt_number
-   proof_url
-   proof_type
-   description
-   submitted_at
-   status

### VERIFICATION_REVIEWS

-   id
-   submission_id
-   reviewer_id
-   decision
-   comments
-   reviewed_at

### XP_TRANSACTIONS

-   id
-   user_id
-   season_id
-   submission_id
-   points
-   transaction_type
-   description
-   created_at

Every reward or adjustment must have a traceable transaction. Use a
unique idempotency key or equivalent database constraint to prevent
duplicate rewards for the same qualifying event.

### STREAKS

-   id
-   user_id
-   group_id
-   current_count
-   longest_count
-   last_qualified_date
-   updated_at

### AVATARS

-   id
-   name
-   asset_url
-   unlock_level
-   is_active

### ACHIEVEMENTS

-   id
-   name
-   description
-   condition_config
-   xp_reward
-   asset_url

### USER_ACHIEVEMENTS

-   id
-   user_id
-   achievement_id
-   unlocked_at

Constraint: `UNIQUE(user_id, achievement_id)`.

### RACE_POSITIONS

-   id
-   user_id
-   season_id
-   total_xp
-   distance_percentage
-   updated_at

Constraint: `UNIQUE(user_id, season_id)`.

Treat this table as a cached projection. XP transactions and season
records remain authoritative.

### NOTIFICATIONS

-   id
-   user_id
-   notification_type
-   title
-   message
-   is_read
-   created_at

### AUDIT_LOGS

-   id
-   actor_id
-   action
-   entity_type
-   entity_id
-   metadata
-   created_at

Do not store passwords, session tokens, or other secrets in audit
metadata.

### AUTH_SESSIONS

-   id
-   user_id
-   refresh_token_hash
-   expires_at
-   revoked_at
-   created_at
-   last_used_at

### EMAIL_VERIFICATION_TOKENS

-   id
-   user_id
-   token_hash
-   expires_at
-   used_at

### PASSWORD_RESET_TOKENS

-   id
-   user_id
-   token_hash
-   expires_at
-   used_at

## 3. Core Relationships

``` text
USERS
  |
  +---- GROUP_MEMBERS ---- GROUPS
  |                          |
  |                          +---- SEASONS
  |                          |       |
  |                          |       +---- SEASON_MEMBERS
  |                          |
  |                          +---- CHALLENGES
  |                                  |
  |                                  +---- CHALLENGE_ASSIGNMENTS
  |                                            |
  |                                            +---- SUBMISSIONS
  |                                            |       |
  |                                            |       +---- VERIFICATION_REVIEWS
  |                                            |
  |                                            +---- XP_TRANSACTIONS
  |
  +---- STREAKS
  +---- USER_ACHIEVEMENTS
  +---- AUTH_SESSIONS
  +---- NOTIFICATIONS
  +---- RACE_POSITIONS
```

## 4. API Standards

Base URL: `/api/v1`

All endpoints must validate request bodies, authenticated identity, and
resource-level authorization. Return consistent errors, support
pagination where appropriate, and avoid leaking internal database
information.

### Authentication APIs

  Method   Endpoint
  -------- -----------------------------
  POST     `/auth/register`
  POST     `/auth/login`
  POST     `/auth/logout`
  POST     `/auth/refresh`
  POST     `/auth/verify-email`
  POST     `/auth/resend-verification`
  POST     `/auth/forgot-password`
  POST     `/auth/reset-password`
  GET      `/auth/sessions`
  DELETE   `/auth/sessions/{id}`

### User APIs

  Method   Endpoint
  -------- ------------------------------
  GET      `/users/me`
  PATCH    `/users/me`
  GET      `/users/me/stats`
  GET      `/users/me/achievements`
  GET      `/users/{id}/public-profile`

### Group APIs

  Method   Endpoint
  -------- ----------------------------------
  POST     `/groups`
  GET      `/groups`
  GET      `/groups/{id}`
  POST     `/groups/{id}/invitations`
  POST     `/groups/join`
  GET      `/groups/{id}/members`
  PATCH    `/groups/{id}/members/{user_id}`
  DELETE   `/groups/{id}/members/{user_id}`

### Season APIs

  Method   Endpoint
  -------- -----------------------------
  POST     `/groups/{id}/seasons`
  GET      `/groups/{id}/seasons`
  GET      `/seasons/{id}`
  POST     `/seasons/{id}/join`
  GET      `/seasons/{id}/leaderboard`
  GET      `/seasons/{id}/race`
  GET      `/seasons/{id}/results`

### Challenge APIs

  Method   Endpoint
  -------- --------------------------------
  POST     `/groups/{id}/challenges`
  GET      `/groups/{id}/challenges`
  GET      `/challenges/{id}`
  PATCH    `/challenges/{id}`
  POST     `/challenges/{id}/publish`
  POST     `/challenges/{id}/assignments`
  GET      `/challenges/daily`
  POST     `/ai/challenges/generate`

### Submission APIs

  Method   Endpoint
  -------- ---------------------------------
  POST     `/submissions/upload-url`
  POST     `/assignments/{id}/submissions`
  GET      `/submissions/{id}`
  GET      `/groups/{id}/reviews/pending`
  POST     `/submissions/{id}/reviews`
  POST     `/submissions/{id}/disputes`

### Game APIs

  Method   Endpoint
  -------- --------------------------------
  GET      `/game/profile/{user_id}`
  GET      `/game/leaderboard/{group_id}`
  GET      `/game/streaks`
  GET      `/game/achievements`
  GET      `/game/xp-history`
  GET      `/game/race/{season_id}`

## 5. Standard API Response

Success:

``` json
{
  "success": true,
  "data": {
    "message": "Submission approved"
  },
  "error": null
}
```

Error:

``` json
{
  "success": false,
  "data": null,
  "error": {
    "code": "FORBIDDEN",
    "message": "You cannot access this resource"
  }
}
```

Suggested HTTP status codes: - 200: Success. - 201: Created. - 204:
Successful operation without response body. - 400: Invalid request. -
401: Unauthenticated. - 403: Unauthorized. - 404: Not found. - 409:
Conflict. - 422: Validation error. - 429: Rate limit exceeded. - 500:
Unexpected server error.

## 6. Core Business Rules

### XP

-   XP is calculated on the backend.
-   Approved submissions award XP.
-   Duplicate awards are prohibited.
-   Manual adjustments require authorization and audit logs.
-   XP transactions must be traceable.

### Streaks

-   Use the configured group or user timezone.
-   A qualifying daily completion maintains a streak.
-   Missing a required calendar day breaks the streak.
-   Define daily qualification rules before season launch.

### Race

-   Season XP determines race progress.
-   Race position is recalculated from authoritative XP.
-   Clients cannot submit their own XP or distance.
-   All participants use the same track scale within a season.

### Season

-   Season membership follows configured joining rules.
-   Season start and end dates are explicit.
-   Final scores are calculated from qualifying transactions.
-   Rankings become immutable after finalization, except for controlled
    audited corrections.

### Verification

-   Users cannot review their own submissions.
-   Only authorized group members can review.
-   Each assignment has defined attempt limits.
-   Disputes can be reviewed by an admin.
-   A submission can earn XP only once.

## 7. WebSocket Events

Example:

``` json
{
  "event": "race.position_updated",
  "group_id": "uuid",
  "season_id": "uuid",
  "user_id": "uuid",
  "total_xp": 1250,
  "distance_percentage": 62.5
}
```

Event types: - `challenge.published` - `submission.created` -
`submission.approved` - `submission.rejected` - `xp.updated` -
`streak.updated` - `race.position_updated` - `leaderboard.updated` -
`member.joined`

Events must be published after successful database commits.

## 8. API Acceptance Criteria

-   All protected endpoints require valid authentication.
-   Group data is isolated between groups.
-   Users cannot manipulate XP through requests.
-   Duplicate approvals cannot produce duplicate rewards.
-   Unauthorized resource access returns appropriate errors.
-   All API contracts are documented in OpenAPI.
-   Database migrations support fresh and existing environments.
-   Integration tests cover authentication, groups, submissions, and
    scoring.
