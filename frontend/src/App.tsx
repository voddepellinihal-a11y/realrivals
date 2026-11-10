import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import Dashboard from "./components/Dashboard";

type View =
  | "landing"
  | "login"
  | "verify-email"
  | "forgot-password"
  | "reset-password"
  | "onboarding"
  | "dashboard"
  | "routines";

interface Routine {
  id: string;
  title: string;
  time: string;
  frequency: string;
  notes: string;
  category?: string;
  xp?: number;
  completed?: boolean;
}

const TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Asia/Kolkata",
  "Australia/Sydney",
];

/* ------------------------------------------------------------------ */
/* Shared brand-palette building blocks                                */
/* ------------------------------------------------------------------ */

const inputCls =
  "w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-accent focus:outline-none";

const actionBtnCls =
  "w-full rounded-lg bg-brand-action px-6 py-3 font-bold text-white transition hover:bg-brand-action-dark disabled:opacity-60";

const accentBtnCls =
  "w-full rounded-lg bg-brand-accent px-6 py-3 font-bold text-brand-base transition hover:bg-brand-accent-soft disabled:opacity-60";

function Screen({
  title,
  subtitle,
  accent = "amber",
  children,
}: {
  title: string;
  subtitle: string;
  accent?: "amber" | "blue";
  children: ReactNode;
}) {
  const accentText = accent === "amber" ? "text-brand-accent" : "text-brand-action";
  return (
    <div className="min-h-screen bg-brand-base text-slate-100">
      <main className="mx-auto flex max-w-md flex-col px-6 py-24">
        <div className="rounded-2xl border border-brand-edge bg-brand-surface p-8">
          <p className="text-[10px] uppercase tracking-widest text-slate-500">Real-Life Rivals</p>
          <h1 className={`mt-2 text-3xl font-bold ${accentText}`}>{title}</h1>
          <p className="mt-2 text-sm text-slate-400">{subtitle}</p>
          <div className="mt-8 space-y-4">{children}</div>
        </div>
      </main>
    </div>
  );
}

function StatusMessages({ error, message }: { error: string | null; message: string | null }) {
  return (
    <>
      {error && (
        <p className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}
      {message && (
        <p className="mt-4 rounded-lg border border-brand-accent bg-brand-accent/10 px-4 py-3 text-sm font-semibold text-brand-accent">
          {message}
        </p>
      )}
    </>
  );
}

/* ------------------------------------------------------------------ */

export default function App() {
  const [view, setView] = useState<View>("landing");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Onboarding state
  const [fullName, setFullName] = useState("");
  const [onboardUsername, setOnboardUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [avatarId, setAvatarId] = useState("");

  // Routines view state
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [routineTitle, setRoutineTitle] = useState("");
  const [routineTime, setRoutineTime] = useState("08:00");
  const [routineFrequency, setRoutineFrequency] = useState("daily");
  const [routinesBusy, setRoutinesBusy] = useState(false);

  const api = async (path: string, body?: unknown, method?: string) => {
    const res = await fetch(path, {
      method: method ?? (body ? "POST" : "GET"),
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 503) {
        throw new Error("Database not connected. Check your Supabase credentials / network.");
      }
      throw new Error((data as { detail?: string }).detail || `Request failed (${res.status})`);
    }
    return data;
  };

  // Session check — land straight on the dashboard if a session already exists.
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const res = await fetch("/auth/me", { credentials: "include" });
        if (!res.ok || cancelled) return;
        const data = await res.json().catch(() => ({}));
        if (data?.user) {
          setView(data.user.profile_setup_complete === false ? "onboarding" : "dashboard");
        }
      } catch {
        /* not logged in — stay on landing */
      }
    };
    check();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const data = await api("/auth/login", { email, password });
      if (data.user?.profile_setup_complete === false) {
        setOnboardUsername(data.user?.username || "");
        setView("onboarding");
      } else {
        setView("dashboard");
      }
      setEmail("");
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  const handleVerifyEmail = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const data = await api("/auth/verify-email", { token });
      setMessage(data.message ?? "Email verified");
      setView("login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setBusy(false);
    }
  };

  const handleForgotPassword = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const data = await api("/auth/forgot-password", { email });
      setMessage(data.message ?? "Password reset email sent");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send reset email");
    } finally {
      setBusy(false);
    }
  };

  const handleResetPassword = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const data = await api("/auth/reset-password", { token, password });
      setMessage(data.message ?? "Password reset successfully");
      setView("login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setBusy(false);
    }
  };

  const handleOnboarding = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const data = await api("/auth/onboarding", {
        full_name: fullName,
        username: onboardUsername,
        new_password: newPassword,
        timezone: timezone,
        avatar_id: avatarId || null,
      });
      setMessage(data.message ?? "Onboarding complete!");
      setView("dashboard");
      setFullName("");
      setOnboardUsername("");
      setNewPassword("");
      setTimezone("UTC");
      setAvatarId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Onboarding failed");
    } finally {
      setBusy(false);
    }
  };

  const handleCreateRoutine = async (e: FormEvent) => {
    e.preventDefault();
    setRoutinesBusy(true);
    setError(null);
    setMessage(null);
    try {
      const data = await api("/routines", {
        title: routineTitle,
        time: routineTime,
        frequency: routineFrequency,
        category: "health",
        xp: 25,
      });
      setRoutines((prev) => (Array.isArray(data) ? [...prev, ...data] : [...prev, data]));
      setMessage(`Routine "${data?.title ?? routineTitle}" added.`);
      setRoutineTitle("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add routine");
    } finally {
      setRoutinesBusy(false);
    }
  };

  /* ---------------------------------------------------------------- */
  /* Onboarding                                                        */
  /* ---------------------------------------------------------------- */
  if (view === "onboarding") {
    return (
      <Screen
        title="Welcome! Let's set up your profile"
        subtitle="Complete your setup to start competing."
        accent="amber"
      >
        <form className="space-y-4" onSubmit={handleOnboarding}>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Full name / Display name"
            className={inputCls}
          />
          <input
            type="text"
            required
            minLength={3}
            maxLength={30}
            value={onboardUsername}
            onChange={(e) => setOnboardUsername(e.target.value)}
            placeholder="Username (3-30 chars)"
            className={inputCls}
          />
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New password (min 8 chars)"
            className={inputCls}
          />
          <select value={timezone} onChange={(e) => setTimezone(e.target.value)} className={inputCls}>
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>{tz}</option>
            ))}
          </select>
          <input
            type="text"
            value={avatarId}
            onChange={(e) => setAvatarId(e.target.value)}
            placeholder="Avatar ID (optional)"
            className={inputCls}
          />
          <button type="submit" disabled={busy} className={accentBtnCls}>
            {busy ? "Saving…" : "Complete Setup"}
          </button>
        </form>
        <StatusMessages error={error} message={message} />
      </Screen>
    );
  }

  /* ---------------------------------------------------------------- */
  /* Login                                                             */
  /* ---------------------------------------------------------------- */
  if (view === "login") {
    return (
      <Screen title="Welcome back" subtitle="Log in to your Real-Life Rivals account." accent="blue">
        <form className="space-y-4" onSubmit={handleLogin}>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className={inputCls}
          />
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className={inputCls}
          />
          <button type="submit" disabled={busy} className={actionBtnCls}>
            {busy ? "Logging in…" : "Log in"}
          </button>
        </form>
        <StatusMessages error={error} message={message} />
        <div className="flex gap-4 text-sm">
          <button className="text-slate-400 underline hover:text-brand-accent" onClick={() => setView("forgot-password")}>
            Forgot password
          </button>
          <button className="text-slate-400 underline hover:text-brand-accent" onClick={() => setView("verify-email")}>
            Verify email
          </button>
        </div>
        <button className="text-sm text-slate-400 underline hover:text-brand-accent" onClick={() => setView("landing")}>
          Back to home
        </button>
      </Screen>
    );
  }

  /* ---------------------------------------------------------------- */
  /* Verify email                                                      */
  /* ---------------------------------------------------------------- */
  if (view === "verify-email") {
    return (
      <Screen
        title="Verify your email"
        subtitle="Enter the verification token from your email to activate your account."
        accent="amber"
      >
        <form className="space-y-4" onSubmit={handleVerifyEmail}>
          <input
            type="text"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Verification token"
            className={inputCls}
          />
          <button type="submit" disabled={busy} className={accentBtnCls}>
            {busy ? "Verifying…" : "Verify email"}
          </button>
        </form>
        <StatusMessages error={error} message={message} />
        <button className="text-sm text-slate-400 underline hover:text-brand-accent" onClick={() => setView("login")}>
          Back to login
        </button>
      </Screen>
    );
  }

  /* ---------------------------------------------------------------- */
  /* Forgot password                                                   */
  /* ---------------------------------------------------------------- */
  if (view === "forgot-password") {
    return (
      <Screen title="Forgot password" subtitle="Enter your email and we'll send a reset link." accent="blue">
        <form className="space-y-4" onSubmit={handleForgotPassword}>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className={inputCls}
          />
          <button type="submit" disabled={busy} className={actionBtnCls}>
            {busy ? "Sending…" : "Send reset link"}
          </button>
        </form>
        <StatusMessages error={error} message={message} />
        <button className="text-sm text-slate-400 underline hover:text-brand-accent" onClick={() => setView("login")}>
          Back to login
        </button>
      </Screen>
    );
  }

  /* ---------------------------------------------------------------- */
  /* Reset password                                                    */
  /* ---------------------------------------------------------------- */
  if (view === "reset-password") {
    return (
      <Screen title="Reset password" subtitle="Enter your reset token and choose a new password." accent="amber">
        <form className="space-y-4" onSubmit={handleResetPassword}>
          <input
            type="text"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Reset token"
            className={inputCls}
          />
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="New password (min 8 chars)"
            className={inputCls}
          />
          <button type="submit" disabled={busy} className={accentBtnCls}>
            {busy ? "Resetting…" : "Reset password"}
          </button>
        </form>
        <StatusMessages error={error} message={message} />
        <button className="text-sm text-slate-400 underline hover:text-brand-accent" onClick={() => setView("login")}>
          Back to login
        </button>
      </Screen>
    );
  }

  /* ---------------------------------------------------------------- */
  /* Routines (standalone view)                                        */
  /* ---------------------------------------------------------------- */
  if (view === "routines") {
    return (
      <div className="min-h-screen bg-brand-base text-slate-100">
        <main className="mx-auto max-w-2xl px-6 py-24">
          <h1 className="text-3xl font-bold text-brand-accent">Your routines</h1>
          <p className="mt-2 text-sm text-slate-400">
            Add daily routines like "wake up at 5" and track them.
          </p>

          <form
            className="mt-8 space-y-4 rounded-xl border border-brand-edge bg-brand-surface p-6"
            onSubmit={handleCreateRoutine}
          >
            <h2 className="text-lg font-semibold text-brand-accent">Add routine</h2>
            <input
              type="text"
              required
              value={routineTitle}
              onChange={(e) => setRoutineTitle(e.target.value)}
              placeholder="Routine title (e.g. Wake up at 05:00)"
              className={inputCls}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <input type="time" required value={routineTime} onChange={(e) => setRoutineTime(e.target.value)} className={inputCls} />
              <select value={routineFrequency} onChange={(e) => setRoutineFrequency(e.target.value)} className={inputCls}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <button type="submit" disabled={routinesBusy} className={accentBtnCls}>
              {routinesBusy ? "Adding…" : "Add routine"}
            </button>
          </form>

          <StatusMessages error={error} message={message} />

          <div className="mt-8 space-y-3">
            {routines.length === 0 && <p className="text-sm text-slate-400">No routines yet.</p>}
            {routines.map((r) => (
              <div key={r.id} className="rounded-xl border border-brand-edge bg-brand-surface p-4">
                <p className="font-semibold text-brand-accent">{r.title}</p>
                <p className="mt-1 text-sm text-slate-400">
                  {r.time} · {r.frequency}
                </p>
              </div>
            ))}
          </div>

          <button className="mt-8 text-sm text-slate-400 underline hover:text-brand-accent" onClick={() => setView("landing")}>
            Back to home
          </button>
        </main>
      </div>
    );
  }

  /* ---------------------------------------------------------------- */
  /* Dashboard                                                         */
  /* ---------------------------------------------------------------- */
  if (view === "dashboard") {
    return <Dashboard onNavigate={(v) => setView(v as View)} />;
  }

  /* ---------------------------------------------------------------- */
  /* Landing page                                                      */
  /* ---------------------------------------------------------------- */
  return (
    <div className="min-h-screen bg-brand-base text-slate-100">
      <header className="border-b border-brand-edge bg-brand-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-brand-action bg-brand-action text-xl">
              ⚔️
            </div>
            <span className="text-lg font-extrabold tracking-wide text-white">Real-Life Rivals</span>
          </div>
          <button
            onClick={() => setView("login")}
            className="rounded-lg bg-brand-action px-5 py-2.5 text-sm font-bold text-white transition hover:bg-brand-action-dark"
          >
            Log in
          </button>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col items-center px-6 py-24 text-center">
        <p className="mb-4 text-sm font-semibold uppercase tracking-widest text-brand-accent">
          Multiplayer real-world challenges
        </p>
        <h1 className="text-5xl font-extrabold text-white sm:text-6xl">Level Up Your Real Life.</h1>
        <p className="mt-6 max-w-2xl text-lg text-slate-400">
          Real-Life Rivals turns everyday activities, habits, and productivity into friendly
          competition. Build routines, take on daily challenges, submit proof, earn XP, and go
          head-to-head with a rival on a shared leaderboard.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={() => setView("login")}
            className="rounded-lg bg-brand-action px-6 py-3 font-bold text-white transition hover:bg-brand-action-dark"
          >
            Enter the Arena
          </button>
          <a
            href="#how"
            className="rounded-lg border border-brand-accent bg-brand-accent/10 px-6 py-3 font-semibold text-brand-accent transition hover:bg-brand-accent/20"
          >
            How it works
          </a>
        </div>
      </main>

      <section id="how" className="mx-auto max-w-5xl px-6 py-16">
        <h2 className="text-3xl font-bold text-brand-accent">How it works</h2>
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ["Daily challenges", "Small real-world goals you can take on and track to the finish line."],
            ["Photo proof", "Submit a photo, text, or link as proof and let your rival verify it."],
            ["XP & streaks", "Earn XP, keep streaks alive, and level up through the season."],
            ["Rival duels", "Challenge one opponent head-to-head and settle it with verified proof."],
            ["Personal biometrics", "Log height, weight, and target to see your BMI update live."],
            ["Seasons", "Recurring competitions with final rankings and trophies."],
          ].map(([title, body]) => (
            <div key={title} className="rounded-xl border border-brand-edge bg-brand-surface p-6">
              <h3 className="text-lg font-semibold text-brand-accent">{title}</h3>
              <p className="mt-2 text-sm text-slate-400">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="join" className="mx-auto max-w-5xl px-6 py-16 text-center">
        <h2 className="text-3xl font-bold text-brand-action">Ready to level up?</h2>
        <p className="mt-4 text-slate-400">
          This instance is private — sign in with the account your rival group gave you.
        </p>
        <button
          onClick={() => setView("login")}
          className="mt-8 rounded-lg bg-brand-action px-8 py-3 font-bold text-white transition hover:bg-brand-action-dark"
        >
          Log in to your account
        </button>
      </section>

      <footer className="border-t border-brand-edge bg-brand-surface">
        <div className="mx-auto max-w-5xl px-6 py-8 text-center text-xs uppercase tracking-widest text-slate-600">
          Real-Life Rivals — private instance
        </div>
      </footer>
    </div>
  );
}
