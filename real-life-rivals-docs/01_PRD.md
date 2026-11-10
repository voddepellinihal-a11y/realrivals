# REAL-LIFE RIVALS

## Product Requirements Document (PRD)

**Version:** 1.0\
**Product:** Real-Life Rivals\
**Tagline:** Level Up Your Real Life.\
**Platform:** Responsive, login-required web application\
**Initial season target:** January 1, 2027 (configurable)

## 1. Product Overview

Real-Life Rivals is a multiplayer real-world challenge platform where
friends compete by completing everyday activities, building habits, and
improving productivity. Users create private groups, invite friends,
participate in shared and personalized daily challenges, submit
completion evidence, earn XP, maintain streaks, unlock achievements, and
race together on a common virtual track.

The product combines real-world productivity, social competition, and
game mechanics.

## 2. Product Objectives

1.  Encourage consistency and productivity through friendly competition.
2.  Make daily routines enjoyable through gamification.
3.  Allow friends to compete in private groups.
4.  Provide transparent task verification and scoring.
5.  Create a shared multiplayer race experience.
6.  Use AI to suggest personalized and group challenges.
7.  Support recurring competition seasons.

## 3. Target Users

-   College students and friend groups.
-   Fitness and productivity enthusiasts.
-   People interested in habit building.
-   Small private communities.

Initial target: 4--15 users per private group.

## 4. User Roles

### Registered User

-   Create and manage a profile.
-   Select and customize an avatar.
-   Create or join private groups.
-   Participate in challenges.
-   Submit proof and review assigned submissions.
-   Earn XP, levels, streaks, and achievements.
-   View leaderboards and race progress.

### Group Administrator

-   Create and manage groups.
-   Invite and remove members.
-   Create and publish challenges.
-   Assign tasks and review submissions.
-   Resolve disputes.
-   Configure competition seasons.
-   View group analytics.

### AI Assistant

-   Generate challenge suggestions.
-   Recommend difficulty levels.
-   Suggest personalized challenges.
-   Analyze group participation.
-   Flag potentially suspicious submissions for human review.

AI cannot independently modify XP, approve submissions, or override
group permissions.

## 5. Functional Requirements

### FR-01: Authentication

-   Registration using email and password.
-   Mandatory email verification.
-   Secure login and logout.
-   Forgot-password and reset-password functionality.
-   Secure session management.
-   Account profile management.
-   Protected application routes.

### FR-02: User Profiles

-   Username and profile picture.
-   Avatar selection.
-   XP and level.
-   Current and longest streak.
-   Achievements and competition history.

### FR-03: Groups

-   Create private groups.
-   Join using invitation codes or links.
-   Manage group members and administrators.
-   Display group activity.
-   Support multiple groups per user.

### FR-04: Challenge Management

-   Common group challenges.
-   Individual personalized challenges.
-   Admin-created challenges.
-   Friend-created challenge suggestions.
-   AI-generated challenge suggestions.
-   Categories, difficulty, deadlines, and completion limits.

### FR-05: Proof Submission

-   Photo evidence in MVP.
-   Video evidence in a later release.
-   Timer-based records.
-   GPS evidence where relevant and permissioned.
-   Friend verification.
-   Admin dispute resolution.

### FR-06: Gamification

-   XP rewards and user levels.
-   Daily streaks.
-   Weekly achievements.
-   Badges and trophies.
-   Season-based rankings.

### FR-07: Multiplayer Race

-   One common racing track per season.
-   All group members represented by avatars.
-   Avatar movement based on verified season XP.
-   Live leaderboard updates.
-   Race position synchronization.
-   Finish-line celebrations.

### FR-08: AI Challenge Generation

-   Generate tasks based on user interests.
-   Generate common group challenges.
-   Suggest challenge difficulty and XP.
-   Validate AI-generated challenge data.
-   Require authorized publication.

### FR-09: Notifications

-   New challenge notifications.
-   Submission approval/rejection.
-   Streak reminders.
-   Friend invitations.
-   Leaderboard changes.
-   Season-ending reminders.

### FR-10: Season Finale

-   Configure start and end dates.
-   Lock scoring at season end.
-   Calculate final standings.
-   Declare first, second, and third place.
-   Award trophies and special achievements.
-   Preserve historical results.

## 6. Challenge Categories

-   Study and learning.
-   Fitness and exercise.
-   Reading and knowledge.
-   Morning and evening routines.
-   Productivity.
-   Personal development.
-   Daily responsibilities.
-   Custom challenges.

## 7. MVP Scope

The first production release must include:

1.  Registration and secure login.
2.  Email verification.
3.  User profiles and avatars.
4.  Private groups and invitations.
5.  Group and individual challenges.
6.  Photo proof submission.
7.  Friend and admin verification.
8.  XP and streak calculations.
9.  Leaderboard.
10. Multiplayer race track.
11. New Year countdown.
12. Basic achievements.
13. Admin dashboard.
14. Responsive desktop and mobile UI.

AI challenge generation should follow once the core competition engine
is stable.

## 8. Out of Scope for MVP

-   Public global competitions.
-   Financial betting or real-money rewards.
-   Native Android/iOS applications.
-   Advanced computer-vision verification.
-   Complex avatar marketplaces.
-   Subscription payments.

## 9. Non-Functional Requirements

-   Secure authentication and authorization.
-   Responsive design.
-   Consistent server-side scoring.
-   No duplicate XP awards.
-   Reliable database transactions.
-   Secure proof storage.
-   Real-time race updates.
-   Error handling and recovery.
-   Database backups.
-   Production logging and monitoring.

## 10. Success Metrics

-   Registered users.
-   Active groups.
-   Daily active participants.
-   Daily challenge completion rate.
-   Weekly user retention.
-   Average streak duration.
-   Percentage of verified submissions.
-   Race participation.
-   Completed seasons.

## 11. Product Acceptance Criteria

The MVP is accepted when a user can register, verify an email, log in,
create or join a group, receive challenges, submit evidence, obtain
verification, earn XP, maintain a streak, and see their avatar move on
the shared race track.

All competition data must persist after logout, refresh, and deployment
restarts.
