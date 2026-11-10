# REAL-LIFE RIVALS

## UI/UX & Design System Specification

**Version:** 1.0\
**Design Direction:** Premium Multiplayer Gaming + Productivity\
**Framework:** React + Tailwind CSS + Framer Motion

## 1. Brand Identity

**Product name:** Real-Life Rivals\
**Tagline:** Level Up Your Real Life.

The application should feel like a modern multiplayer game rather than a
conventional habit-tracking website.

### Design principles

-   Competitive but friendly.
-   Playful but professional.
-   Visually rich but easy to navigate.
-   Animated but performance-conscious.
-   Clear progress indicators.
-   Consistent design across desktop and mobile.

## 2. Color Palette

  Purpose                Color             Hex
  ---------------------- ----------------- -----------
  Main background        Deep Navy         `#101426`
  Secondary background   Dark Slate        `#191F35`
  Card background        Slate             `#222B45`
  Primary accent         Electric Purple   `#8B5CF6`
  Secondary accent       Neon Green        `#A3E635`
  XP accent              Gold              `#FBBF24`
  Information            Blue              `#60A5FA`
  Success                Green             `#22C55E`
  Warning                Orange            `#F59E0B`
  Error                  Red               `#EF4444`
  Primary text           Off White         `#F8FAFC`
  Secondary text         Muted Slate       `#A1A1AA`

Use accent colors sparingly to maintain readability.

## 3. Typography

Recommended: - Headings: Space Grotesk. - Body: Inter. - Numbers and
scores: Space Grotesk with tabular numerals.

Hierarchy: - Page heading: 32--40px desktop. - Section heading:
22--26px. - Card heading: 16--20px. - Body: 14--16px. - Supporting
labels: 12--13px.

## 4. Global Navigation

### Desktop sidebar

1.  Dashboard.
2.  Race Arena.
3.  Challenges.
4.  Leaderboard.
5.  Friends & Groups.
6.  Achievements.
7.  Profile.
8.  Settings.

Admin-only: - Group Management. - Challenge Management. - Submission
Reviews. - Season Management.

Top navigation: - Group selector. - Notification center. - Season
countdown. - User avatar menu.

Mobile navigation: - Bottom navigation with Dashboard, Race, Challenges,
Leaderboard, and Profile. - Secondary pages accessible through menus.

## 5. Application Screens

### Screen 01: Landing Page

Route: `/`

-   Brand introduction.
-   Hero animation with running avatars.
-   Product description.
-   How it works.
-   Feature highlights.
-   Login and registration calls to action.

Public visitors can see this page but cannot access competition data.

### Screen 02: Login

Route: `/login`

-   Email.
-   Password.
-   Show/hide password.
-   Forgot password.
-   Login button.
-   Registration link.
-   Validation messages.
-   Login error feedback.

### Screen 03: Registration

Route: `/register`

-   Username.
-   Email.
-   Password.
-   Confirm password.
-   Terms and privacy acceptance.
-   Create account button.

After registration, show email-verification instructions.

### Screen 04: Email Verification

Route: `/verify-email`

-   Verification status.
-   Resend verification email.
-   Continue to onboarding after successful verification.

### Screen 05: Onboarding

Route: `/onboarding`

1.  Choose username.
2.  Choose avatar.
3.  Select interests.
4.  Select challenge categories.
5.  Create or join a group.
6.  Complete profile setup.

### Screen 06: Dashboard

Route: `/dashboard`

-   Greeting and avatar.
-   Current level and XP.
-   Streak counter.
-   Daily progress bar.
-   Today's common challenges.
-   Today's personal challenges.
-   Race preview.
-   Group leaderboard preview.
-   Countdown.
-   Recent friend activity.

### Screen 07: Race Arena

Route: `/race`

-   Multiplayer racing track.
-   Animated avatar characters.
-   Player names and race positions.
-   XP totals and progress percentage.
-   Finish line and countdown.
-   Live leaderboard.

Animations: - Running idle animation. - Position update. - Overtaking
effect. - XP gain effect. - Season completion celebration.

The track must work on mobile without excessive horizontal scrolling.

### Screen 08: Challenge Center

Route: `/challenges`

Tabs: - All. - Group challenges. - Personal challenges. - Completed. -
Expired.

Challenge cards show title, description, category, difficulty, XP,
deadline, proof requirement, and completion status.

### Screen 09: Challenge Details

Route: `/challenges/:id`

-   Full description.
-   Rules.
-   Reward.
-   Deadline.
-   Participants.
-   Submission action.
-   Verification method.
-   Submission history.

### Screen 10: Submission Center

Route: `/submissions`

-   Upload proof.
-   Description.
-   Preview.
-   Submission history.
-   Review status.
-   Resubmission where allowed.

### Screen 11: Leaderboard

Route: `/leaderboard`

-   Top-three podium.
-   Full group ranking.
-   XP.
-   Streaks.
-   Completed tasks.
-   Weekly and season rankings.

### Screen 12: Friends & Groups

Route: `/groups`

-   My groups.
-   Create group.
-   Join group.
-   Invite friends.
-   Group members.
-   Group settings.
-   Group activity.

### Screen 13: Achievements

Route: `/achievements`

-   Locked badges.
-   Unlocked badges.
-   Progress toward next achievement.
-   Level rewards.
-   Special seasonal rewards.

### Screen 14: Profile

Route: `/profile`

-   Avatar.
-   Username.
-   Level.
-   Total XP.
-   Streak history.
-   Achievements.
-   Challenge statistics.
-   Competition history.

### Screen 15: Admin Dashboard

Route: `/admin`

-   Group overview.
-   Member management.
-   Challenge creation.
-   AI challenge suggestions.
-   Submission review.
-   Dispute management.
-   Season configuration.
-   Audit history.

### Screen 16: Settings

Route: `/settings`

-   Account details.
-   Password change.
-   Timezone.
-   Notification preferences.
-   Session management.
-   Privacy settings.
-   Account deletion.

## 6. Component Library

Build reusable components: - `AppSidebar` - `MobileNavigation` -
`TopNavigation` - `UserAvatar` - `LevelProgress` - `XPDisplay` -
`StreakCounter` - `CountdownTimer` - `ChallengeCard` -
`ChallengeCategoryBadge` - `ProofUploader` - `SubmissionStatus` -
`LeaderboardTable` - `RaceTrack` - `RacePlayer` - `AchievementBadge` -
`NotificationPanel` - `GroupCard` - `ConfirmationDialog` -
`LoadingSkeleton` - `EmptyState` - `ErrorState`

## 7. Animation Requirements

Use Framer Motion for: - Page transitions. - Card entrance. - XP
counters. - Progress bars. - Badge unlocks. - Modal transitions. - Race
movement. - Leaderboard reordering.

Use optimized assets for complex 3D characters. Do not use heavy 3D
rendering on every screen.

Respect reduced-motion accessibility settings.

## 8. Responsive Design

Support: - Mobile: 360px and above. - Tablet: 768px and above. -
Desktop: 1024px and above. - Large screens: 1440px and above.

Requirements: - No horizontal overflow. - Touch-friendly controls. -
Readable text. - Mobile-friendly proof uploads. - Responsive race
track. - Accessible navigation. - Proper keyboard focus states.

## 9. Accessibility

-   Semantic HTML.
-   Keyboard navigation.
-   Visible focus indicators.
-   Appropriate color contrast.
-   Form labels.
-   Accessible validation messages.
-   Alternative text for meaningful images.
-   Reduced-motion support.

## 10. UI Acceptance Criteria

-   All screens use a consistent design system.
-   No page is visually disconnected from the product.
-   Loading, error, empty, and success states exist.
-   All navigation links work.
-   Login and registration forms have real validation.
-   Protected screens are inaccessible when logged out.
-   Mobile layout is usable.
-   Important actions provide immediate feedback.
-   Production interfaces use real API data, not hardcoded sample
    scores.
