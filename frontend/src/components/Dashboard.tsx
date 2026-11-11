import { useEffect, useState, type FormEvent } from "react";
import VersusCard from "./VersusCard";
import ProofPreviewModal from "./ProofPreviewModal";
import BiometricsCard from "./BiometricsCard";

type Routine = {
  id?: string;
  title?: string;
  time?: string;
  frequency?: string;
  notes?: string;
  category?: string;
  xp?: number;
  completed?: boolean;
  completed_at?: string | null;
};

interface Challenge {
  id?: string;
  title?: string;
  description?: string;
  category?: string;
  difficulty?: string;
  base_xp?: number;
  challenge_type?: string;
  source_type?: string;
  status?: string;
  proof_required?: string;
  proof_type?: string;
  created_by_me?: boolean;
}

interface VersusChallenge {
  id: string;
  title: string;
  description: string;
  category: string;
  xp_reward: number;
  proof_type: string;
  status: string;
  is_challenger: boolean;
  opponent_id: string;
  opponent_username: string;
  created_at: string;
}

interface ProfileData {
  username?: string;
  level?: number;
  lifetime_xp?: number;
  season_xp?: number;
  current_level_xp?: number;
  next_level_xp?: number;
  progress_percentage?: number;
  // Canonical progression keys (server is the source of truth)
  current_level_min_xp?: number;
  xp_in_level?: number;
  level_xp_span?: number;
  progress_percent?: number;
  current_streak?: number;
  longest_streak?: number;
  height_cm?: number;
  weight_kg?: number;
  target_weight_kg?: number;
  timezone?: string;
  bmi?: number;
  gender?: string;
}

interface DashboardProps {
  onNavigate: (view: string) => void;
}

const CATEGORIES = ["health", "fitness", "productivity", "mindset", "study", "reading"];
const PROOF_TYPES = ["photo", "text", "link"];

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [versusChallenges, setVersusChallenges] = useState<VersusChallenge[]>([]);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [showRoutineModal, setShowRoutineModal] = useState(false);
  const [showChallengeModal, setShowChallengeModal] = useState(false);
  const [showRivalModal, setShowRivalModal] = useState(false);

  // Routine form state
  const [routineTitle, setRoutineTitle] = useState("");
  const [routineCategory, setRoutineCategory] = useState("health");
  const [routineXp, setRoutineXp] = useState(25);
  const [routineTime, setRoutineTime] = useState("08:00");
  const [routineBusy, setRoutineBusy] = useState(false);

  // Challenge form state
  const [challengeTitle, setChallengeTitle] = useState("");
  const [challengeDesc, setChallengeDesc] = useState("");
  const [challengeCategory, setChallengeCategory] = useState("productivity");
  const [challengeXp, setChallengeXp] = useState(40);
  const [challengeProof, setChallengeProof] = useState("photo");
  const [challengeBusy, setChallengeBusy] = useState(false);

  // Rival vs Rival form state
  const [rivalTarget, setRivalTarget] = useState("rival2");
  const [rivalTitle, setRivalTitle] = useState("");
  const [rivalProof, setRivalProof] = useState("photo");
  const [rivalXp, setRivalXp] = useState(100);
  const [rivalBusy, setRivalBusy] = useState(false);

  // Proof modal state
  const [showProofModal, setShowProofModal] = useState(false);
  const [proofChallengeId, setProofChallengeId] = useState<string | null>(null);
  const [proofChallengeTitle, setProofChallengeTitle] = useState("");
  const [proofType, setProofType] = useState<"photo" | "text" | "link">("photo");
  const [proofText, setProofText] = useState("");
  const [proofUrl, setProofUrl] = useState("");
  const [proofFileDataUrl, setProofFileDataUrl] = useState<string | null>(null);
  const [submitProofBusy, setSubmitProofBusy] = useState(false);

  // Preview modal state
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewChallengeId, setPreviewChallengeId] = useState<string | null>(null);
  const [previewChallengeTitle, setPreviewChallengeTitle] = useState("");

  // Biometrics form state
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [targetWeight, setTargetWeight] = useState("");
  const [biometricsBusy, setBiometricsBusy] = useState(false);

  // Edit challenge state
  const [editingChallenge, setEditingChallenge] = useState<Challenge | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editCategory, setEditCategory] = useState("health");
  const [editDifficulty, setEditDifficulty] = useState("medium");
  const [editXp, setEditXp] = useState(40);
  const [editProof, setEditProof] = useState("photo");
  const [editBusy, setEditBusy] = useState(false);

  // Per-row busy flags for routine toggles / removals
  const [busyRoutineId, setBusyRoutineId] = useState<string | null>(null);
  const [busyChallengeId, setBusyChallengeId] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const api = async (path: string, body?: unknown, method?: string) => {
    const res = await fetch(path, {
      method: method ?? (body ? "POST" : "GET"),
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 503) throw new Error("Database not connected.");
      if (res.status === 401) {
        onNavigate("login");
        throw new Error("Session expired — please log in again.");
      }
      throw new Error((data as { detail?: string }).detail || `Request failed (${res.status})`);
    }
    return data;
  };

  // Merge /auth/me (identity + biometrics) with /game/profile (XP, level, streak).
  const mergeProfile = (meData: unknown, gameData: unknown) => {
    const me = (meData as { user?: ProfileData } | null)?.user;
    if (!me) return null;
    const game = (gameData as ProfileData | null) ?? null;
    return {
      ...me,
      ...(game
        ? {
            level: game.level ?? me.level,
            lifetime_xp: game.lifetime_xp ?? me.lifetime_xp,
            season_xp: game.season_xp ?? me.season_xp,
            current_level_xp: game.current_level_xp ?? me.current_level_xp,
            next_level_xp: game.next_level_xp ?? me.next_level_xp,
            progress_percentage: game.progress_percentage ?? me.progress_percentage,
            current_level_min_xp: game.current_level_min_xp ?? me.current_level_min_xp,
            xp_in_level: game.xp_in_level ?? me.xp_in_level,
            level_xp_span: game.level_xp_span ?? me.level_xp_span,
            progress_percent: game.progress_percent ?? me.progress_percent,
            current_streak: game.current_streak ?? me.current_streak,
            longest_streak: game.longest_streak ?? me.longest_streak,
            gender: game.gender ?? me.gender,
          }
        : {}),
    } as ProfileData;
  };

  const refreshProfile = async () => {
    const [meData, gameData] = await Promise.all([
      api("/auth/me").catch(() => null),
      api("/game/profile").catch(() => null),
    ]);
    const merged = mergeProfile(meData, gameData);
    if (merged) setProfile(merged);
    return merged;
  };

  // Load profile + routines + challenges + versus
  useEffect(() => {
    const load = async () => {
      try {
        const [profileData, gameData, routinesData, challengesData, versusData] = await Promise.all([
          api("/auth/me").catch(() => null),
          api("/game/profile").catch(() => null),
          api("/routines").catch(() => []),
          api("/challenges").catch(() => []),
          api("/challenges/versus").catch(() => []),
        ]);
        const merged = mergeProfile(profileData, gameData);
        if (merged) {
          setProfile(merged);
          setHeight(merged.height_cm?.toString() ?? "");
          setWeight(merged.weight_kg?.toString() ?? "");
          setTargetWeight(merged.target_weight_kg?.toString() ?? "");
        }
        setRoutines(Array.isArray(routinesData) ? routinesData : []);
        setChallenges(Array.isArray(challengesData) ? challengesData : []);
        setVersusChallenges(Array.isArray(versusData) ? versusData : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep the XP bar in sync: a rival may approve your proof in another tab,
  // so refresh the profile whenever the user comes back to this window.
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        refreshProfile().catch(() => undefined);
      }
    };
    window.addEventListener("focus", onVisible);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.removeEventListener("focus", onVisible);
      document.removeEventListener("visibilitychange", onVisible);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateRoutine = async (e: FormEvent) => {
    e.preventDefault();
    setRoutineBusy(true);
    setError(null);
    try {
      const data = await api("/routines", {
        title: routineTitle,
        time: routineTime,
        frequency: "daily",
        category: routineCategory,
        xp: routineXp,
      });
      setRoutines((prev) => (Array.isArray(data) ? [...prev, ...data] : [...prev, data]));
      setMessage(`Routine "${data?.title ?? "unnamed"}" created!`);
      setShowRoutineModal(false);
      setRoutineTitle("");
      setRoutineTime("08:00");
      setRoutineXp(25);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create routine");
    } finally {
      setRoutineBusy(false);
    }
  };

  /** Toggle a routine — the server awards the XP and advances the streak. */
  const toggleRoutine = async (routine: Routine) => {
    const id = routine?.id;
    if (!id) return;
    setBusyRoutineId(id);
    setError(null);
    try {
      const data = await api(`/routines/${id}`, { completed: !routine.completed }, "PATCH");
      setRoutines((prev) =>
        prev.map((r) => (r?.id === id ? { ...r, ...data } : r))
      );
      const awarded = data?.xp_awarded ?? 0;
      if (awarded > 0) {
        setMessage(
          `Routine complete! +${awarded} XP${data?.leveled_up ? " — you leveled up!" : ""}`
        );
      } else if (data?.completed) {
        setMessage("Routine already completed today — no extra XP.");
      } else {
        setMessage("Routine marked as not done.");
      }
      await refreshProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update routine");
    } finally {
      setBusyRoutineId(null);
    }
  };

  /** Remove a routine. */
  const removeRoutine = async (routine: Routine) => {
    const id = routine?.id;
    if (!id) return;
    setBusyRoutineId(id);
    setError(null);
    try {
      await api(`/routines/${id}`, undefined, "DELETE");
      setRoutines((prev) => prev.filter((r) => r?.id !== id));
      setMessage(`Routine "${routine.title ?? "unnamed"}" removed.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove routine");
    } finally {
      setBusyRoutineId(null);
    }
  };

  /** Remove a challenge (creator only — the server enforces ownership). */
  const removeChallenge = async (challenge: Challenge) => {
    const id = challenge?.id;
    if (!id) return;
    setBusyChallengeId(id);
    setError(null);
    try {
      await api(`/challenges/${id}`, undefined, "DELETE");
      setChallenges((prev) => prev.filter((c) => c?.id !== id));
      setMessage(`Challenge "${challenge.title ?? "unnamed"}" removed.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove challenge");
    } finally {
      setBusyChallengeId(null);
    }
  };

  /** Open the edit modal for a challenge the user created. */
  const openEditChallenge = (challenge: Challenge) => {
    setEditingChallenge(challenge);
    setEditTitle(challenge?.title ?? "");
    setEditDesc(challenge?.description ?? "");
    setEditCategory(challenge?.category ?? "health");
    setEditDifficulty(challenge?.difficulty ?? "medium");
    setEditXp(challenge?.base_xp ?? 40);
    setEditProof(challenge?.proof_type ?? challenge?.proof_required ?? "photo");
  };

  /** Save the edited challenge. */
  const handleSaveChallengeEdit = async (e: FormEvent) => {
    e.preventDefault();
    const id = editingChallenge?.id;
    if (!id) return;
    setEditBusy(true);
    setError(null);
    try {
      const data = await api(
        `/challenges/${id}`,
        {
          title: editTitle,
          description: editDesc,
          category: editCategory,
          difficulty: editDifficulty,
          base_xp: editXp,
          proof_type: editProof,
        },
        "PATCH"
      );
      setChallenges((prev) =>
        prev.map((c) => (c?.id === id ? { ...c, ...data } : c))
      );
      setVersusChallenges((prev) =>
        prev.map((c) => (c.id === id ? { ...c, ...data, xp_reward: data.base_xp } : c))
      );
      setMessage(`Challenge "${data?.title ?? editTitle}" updated.`);
      setEditingChallenge(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update challenge");
    } finally {
      setEditBusy(false);
    }
  };

  /** Re-read the challenge lists from the server (source of truth). */
  const refreshChallenges = async () => {
    const [challengesData, versusData] = await Promise.all([
      api("/challenges").catch(() => []),
      api("/challenges/versus").catch(() => []),
    ]);
    setChallenges(Array.isArray(challengesData) ? challengesData : []);
    setVersusChallenges(Array.isArray(versusData) ? versusData : []);
  };

  const handleCreateChallenge = async (e: FormEvent) => {
    e.preventDefault();
    setChallengeBusy(true);
    setError(null);
    try {
      const data = await api("/challenges", {
        title: challengeTitle,
        description: challengeDesc,
        category: challengeCategory,
        base_xp: challengeXp,
        challenge_type: "daily",
        source_type: "ADMIN",
        proof_type: challengeProof,
      });
      setChallenges((prev) => (Array.isArray(prev) ? [...prev, data] : [data]));
      await refreshChallenges();
      setMessage(`Challenge "${data?.title ?? "unnamed"}" created!`);
      setShowChallengeModal(false);
      setChallengeTitle("");
      setChallengeDesc("");
      setChallengeXp(40);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create challenge");
    } finally {
      setChallengeBusy(false);
    }
  };

  const handleCreateRivalChallenge = async (e: FormEvent) => {
    e.preventDefault();
    setRivalBusy(true);
    setError(null);
    try {
      const data = await api("/challenges/direct", {
        title: rivalTitle,
        description: "",
        category: "fitness",
        xp_reward: rivalXp,
        proof_type: rivalProof,
        target_username_or_id: rivalTarget,
      });
      setVersusChallenges((prev) => (Array.isArray(prev) ? [...prev, data] : [data]));
      await refreshChallenges();
      setMessage(`Direct challenge sent to ${rivalTarget}!`);
      setShowRivalModal(false);
      setRivalTitle("");
      setRivalProof("photo");
      setRivalXp(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create rival challenge");
    } finally {
      setRivalBusy(false);
    }
  };

  const handleAcceptVersus = async (id: string) => {
    try {
      await api(`/challenges/${id}/accept`, {});
      setVersusChallenges((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: "ACTIVE" } : c))
      );
      setMessage("Challenge accepted! Time to battle.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to accept challenge");
    }
  };

  const handleDeclineVersus = async (id: string) => {
    try {
      await api(`/challenges/${id}/decline`, {});
      setVersusChallenges((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: "DECLINED" } : c))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to decline challenge");
    }
  };

  const openSubmitProof = (challenge: Challenge) => {
    setProofChallengeId(challenge?.id ?? null);
    setProofChallengeTitle(challenge?.title ?? "");
    setProofType("photo");
    setProofText("");
    setProofUrl("");
    setProofFileDataUrl(null);
    setShowProofModal(true);
  };

  const openPreviewProof = (challengeId: string, title?: string) => {
    setPreviewChallengeId(challengeId);
    setPreviewChallengeTitle(title ?? "");
    setShowPreviewModal(true);
  };

  const handleProofFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setProofFileDataUrl(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleSubmitProof = async (e: FormEvent) => {
    e.preventDefault();
    if (!proofChallengeId) return;
    setSubmitProofBusy(true);
    setError(null);
    try {
      const payload: Record<string, string> = {
        challenge_id: proofChallengeId,
        proof_type: proofType,
        proof_text: proofType === "text" ? proofText : "",
        proof_url: proofType === "photo" ? (proofFileDataUrl ?? proofUrl) : proofUrl,
        proof_data_url: proofType === "photo" ? proofFileDataUrl ?? "" : "",
        description: "",
      };
      await api("/submissions", payload);
      setMessage("Proof submitted! Awaiting rival review.");
      await refreshChallenges();
      setShowProofModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit proof");
    } finally {
      setSubmitProofBusy(false);
    }
  };

  const handleSaveBiometrics = async (e: FormEvent) => {
    e.preventDefault();
    setBiometricsBusy(true);
    setError(null);
    try {
      const h = height ? parseFloat(height) : undefined;
      const w = weight ? parseFloat(weight) : undefined;
      const tw = targetWeight ? parseFloat(targetWeight) : undefined;
      const data = await api(
        "/auth/preferences",
        {
          height_cm: h,
          weight_kg: w,
          target_weight_kg: tw,
        },
        "PATCH"
      );
      const bmi = data?.preferences?.bmi ?? null;
      setProfile((prev) =>
        prev
          ? { ...prev, height_cm: h, weight_kg: w, target_weight_kg: tw, bmi }
          : { height_cm: h, weight_kg: w, target_weight_kg: tw, bmi }
      );
      setMessage("Biometrics saved — BMI " + (bmi ?? "N/A"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save biometrics");
    } finally {
      setBiometricsBusy(false);
    }
  };

  // Dynamic XP/level math — the server is the source of truth, with a local
  // fallback that mirrors the canonical service exactly.
  const lifetimeXP = profile?.lifetime_xp ?? 0;
  const level = profile?.level ?? computeLevel(lifetimeXP);
  const { currentLevelXP, nextLevelXP, progressPercent } = resolveProgress(profile, lifetimeXP, level);
  const streak = profile?.current_streak ?? 0;
  const displayName = profile?.username ?? "Player";
  const gender = (profile?.gender ?? "").toLowerCase();
  const avatarSymbol = gender === "female" ? "♀️" : gender === "male" ? "♂️" : "🧍";
  const heightCm = profile?.height_cm ?? null;
  const weightKg = profile?.weight_kg ?? null;
  const targetWeightKg = profile?.target_weight_kg ?? null;
  const bmi = profile?.bmi ?? null;

  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);
  const seasonTarget = new Date("2027-01-01T00:00:00Z");
  const seasonDiff = Math.max(seasonTarget.getTime() - now.getTime(), 0);
  const cdDays = Math.floor(seasonDiff / 86400000);
  const cdHours = Math.floor((seasonDiff % 86400000) / 3600000);
  const bmiBadge = getBmiBadge(bmi);
  const weightDelta =
    weightKg !== null && targetWeightKg !== null
      ? Math.round((targetWeightKg - weightKg) * 10) / 10
      : null;

  return (
    <div className="min-h-screen bg-brand-base text-slate-100">
      {/* Header */}
      <header className="border-b border-brand-edge bg-brand-surface">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-brand-action bg-brand-action text-2xl">
                {avatarSymbol}
              </div>
              <div>
                <h1 className="text-2xl font-extrabold tracking-wide text-white">{displayName}</h1>
                <p className="text-xs uppercase tracking-widest text-slate-400">Rival · Level {level}</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="rounded-full border border-brand-accent bg-brand-accent/10 px-4 py-2 text-xs font-bold text-brand-accent">
                🔥 {streak} Day Streak
              </span>
              <div className="flex items-center gap-2 rounded-full border border-brand-edge bg-brand-base px-4 py-2">
                <span className="text-[10px] uppercase text-slate-400">Season</span>
                <span className="font-mono text-xs font-bold text-brand-accent">
                  {cdDays}d {String(cdHours).padStart(2, "0")}:{String(Math.floor((seasonDiff % 3600000) / 60000)).padStart(2, "0")}:{String(Math.floor((seasonDiff % 60000) / 1000)).padStart(2, "0")}
                </span>
              </div>
              <button
                onClick={() => onNavigate("routines")}
                className="rounded-lg border border-brand-edge-strong px-4 py-2 text-xs font-semibold text-slate-300 hover:border-brand-action hover:text-white"
              >
                Routines
              </button>
            </div>
          </div>

          {/* Dynamic XP Progress Bar */}
          <div className="mt-5">
            <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-400">
              <span>Level {level} → {level + 1}</span>
              <span>{lifetimeXP} XP earned · {currentLevelXP}/{nextLevelXP} XP</span>
            </div>
            <div className="relative mt-2 h-5 w-full rounded-full border border-brand-edge-strong bg-brand-base">
              <div
                className="h-full rounded-full bg-brand-accent transition-all duration-700"
                style={{ width: `${progressPercent}%` }}
              />
              {/* Gender avatar anchored to progress */}
              <div
                className="absolute -top-2 flex h-9 w-9 items-center justify-center rounded-full border-2 border-brand-accent bg-brand-base text-lg transition-all duration-700"
                style={{ left: `calc(${progressPercent}% - 18px)` }}
                title={`${progressPercent.toFixed(1)}% to next level`}
              >
                {avatarSymbol}
              </div>
            </div>
            <p className="mt-1 text-[10px] text-slate-500">{progressPercent.toFixed(1)}% to next level</p>
          </div>
        </div>
      </header>

      {/* Action Bar */}
      <div className="mx-auto max-w-7xl px-6 py-6">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowRoutineModal(true)}
            className="flex items-center gap-2 whitespace-nowrap rounded-lg border border-brand-action/30 bg-brand-action px-5 py-3 font-medium text-sm text-white transition hover:bg-brand-action-dark"
          >
            <span aria-hidden="true" className="w-4 text-center leading-none">+</span>
            Add Routine
          </button>
          <button
            onClick={() => setShowChallengeModal(true)}
            className="flex items-center gap-2 whitespace-nowrap rounded-lg border border-brand-action/30 bg-brand-action px-5 py-3 font-medium text-sm text-white transition hover:bg-brand-action-dark"
          >
            <span aria-hidden="true" className="w-4 text-center leading-none">+</span>
            Create Challenge
          </button>
          <button
            onClick={() => setShowRivalModal(true)}
            className="flex items-center gap-2 whitespace-nowrap rounded-lg border border-brand-action/30 bg-brand-action px-5 py-3 font-medium text-sm text-white transition hover:bg-brand-action-dark"
          >
            <span aria-hidden="true" className="w-4 text-center leading-none">⚔️</span>
            Challenge a Rival
          </button>
        </div>

        {error && (
          <div className="mt-4 border-l-4 border-red-500 bg-brand-surface/80 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}
        {message && (
          <div className="mt-4 border-l-4 border-brand-accent bg-brand-surface/80 px-4 py-3 text-sm font-medium text-brand-accent">
            {message}
          </div>
        )}
      </div>

      {/* Personal Biometrics */}
      <div className="mx-auto max-w-7xl px-6">
        <BiometricsCard
          height={height}
          weight={weight}
          targetWeight={targetWeight}
          onHeightChange={setHeight}
          onWeightChange={setWeight}
          onTargetWeightChange={setTargetWeight}
          onSubmit={handleSaveBiometrics}
          busy={biometricsBusy}
          bmi={bmi}
          bmiBadge={bmiBadge}
          heightCm={heightCm}
          weightKg={weightKg}
          targetWeightKg={targetWeightKg}
          weightDelta={weightDelta}
        />
      </div>

      {/* Two-Column Hub */}
      <div className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Routines */}
          <div className="rounded-2xl border border-brand-edge bg-brand-surface p-5">
            <h2 className="text-xl font-bold text-brand-accent">Today's Routines</h2>
            <p className="mt-1 text-xs text-slate-500">Tick one off to earn XP</p>
            <div className="mt-4 space-y-3">
              {routines.length === 0 && <p className="text-sm text-slate-500">No routines yet. Add one to get started!</p>}
              {routines.map((r, i) => (
                <div
                  key={r?.id ?? i}
                  className={`flex items-center gap-3 rounded-xl border border-brand-edge bg-brand-base p-4 ${r?.completed ? "opacity-60" : ""}`}
                >
                  <button
                    onClick={() => toggleRoutine(r)}
                    disabled={busyRoutineId === r?.id}
                    aria-label={r?.completed ? `Un-complete ${r?.title ?? "routine"}` : `Complete ${r?.title ?? "routine"}`}
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md border-2 transition disabled:opacity-50 ${
                      r?.completed
                        ? "border-brand-accent bg-brand-accent text-brand-base"
                        : "border-slate-600 hover:border-brand-accent"
                    }`}
                  >
                    {r?.completed ? "✓" : ""}
                  </button>
                  <div className="flex-1">
                    <p className={`font-medium text-slate-100 ${r?.completed ? "line-through text-slate-500" : ""}`}>
                      {r?.title ?? "Untitled"}
                    </p>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {r?.category && (
                        <span className="rounded-full bg-brand-accent/15 px-2 py-0.5 text-[10px] text-brand-accent">
                          {r.category}
                        </span>
                      )}
                      {r?.time && (
                        <span className="rounded-full bg-brand-edge px-2 py-0.5 text-[10px] text-slate-400">{r.time}</span>
                      )}
                      <span className="rounded-full bg-brand-accent/15 px-2 py-0.5 text-[10px] font-semibold text-brand-accent">
                        +{r?.xp ?? 25} XP
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => removeRoutine(r)}
                    disabled={busyRoutineId === r?.id}
                    aria-label={`Remove ${r?.title ?? "routine"}`}
                    className="rounded-lg border border-brand-edge px-2.5 py-1.5 text-xs font-bold text-slate-400 transition hover:border-red-500/60 hover:text-red-300 disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Daily Challenges */}
          <div className="rounded-2xl border border-brand-edge bg-brand-surface p-5">
            <h2 className="text-xl font-bold text-brand-action">Active Daily Challenges</h2>
            <p className="mt-1 text-xs text-slate-500">Complete challenges to earn XP</p>
            <div className="mt-4 space-y-3">
              {challenges.length === 0 && <p className="text-sm text-slate-500">No challenges yet. Create one to get started!</p>}
              {challenges.map((c, i) => (
                <div key={c?.id ?? i} className="rounded-xl border border-brand-edge bg-brand-base p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-100">{c?.title ?? "Untitled"}</h3>
                      {c?.description && <p className="mt-1 text-xs text-slate-500">{c.description}</p>}
                    </div>
                    <span className="shrink-0 rounded-full bg-brand-accent/15 px-2 py-0.5 text-xs font-bold text-brand-accent">
                      +{c?.base_xp ?? 40} XP
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className="rounded-full bg-brand-edge px-2 py-0.5 text-[10px] text-slate-400">
                      {c?.category ?? "general"}
                    </span>
                    <span className="rounded-full bg-brand-edge px-2 py-0.5 text-[10px] text-slate-400">
                      {c?.difficulty ?? "medium"}
                    </span>
                    {(c?.proof_required || c?.proof_type) && (
                      <span className="rounded-full bg-brand-action/20 px-2 py-0.5 text-[10px] text-brand-action">
                        Proof: {c?.proof_required ?? c?.proof_type}
                      </span>
                    )}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      onClick={() => openSubmitProof(c)}
                      className="flex-1 rounded-lg bg-brand-action px-4 py-2 text-xs font-bold text-white transition hover:bg-brand-action-dark"
                    >
                      Submit Proof
                    </button>
                    <button
                      onClick={() => c?.id && openPreviewProof(c.id, c.title)}
                      className="flex-1 rounded-lg border border-brand-edge-strong px-4 py-2 text-xs font-bold text-slate-300 transition hover:border-brand-action hover:text-white"
                    >
                      View Proof
                    </button>
                    {c?.created_by_me && (
                      <>
                        <button
                          onClick={() => openEditChallenge(c)}
                          aria-label={`Edit ${c?.title ?? "challenge"}`}
                          className="rounded-lg border border-brand-action px-3 py-2 text-xs font-bold text-brand-action transition hover:bg-brand-action/10"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => removeChallenge(c)}
                          disabled={busyChallengeId === c?.id}
                          aria-label={`Remove ${c?.title ?? "challenge"}`}
                          className="rounded-lg border border-brand-edge px-3 py-2 text-xs font-bold text-slate-400 transition hover:border-red-500/60 hover:text-red-300 disabled:opacity-50"
                        >
                          Remove
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Versus Battles */}
      <div className="mx-auto max-w-7xl px-6 pb-12">
        <h2 className="text-2xl font-bold text-brand-action">⚔️ Rival vs Rival Battles</h2>
        <p className="mt-1 text-xs text-slate-500">Direct head-to-head challenges</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {versusChallenges.length === 0 && (
            <p className="text-sm text-slate-500">No rival battles yet. Challenge a rival to get started!</p>
          )}
          {versusChallenges.map((vc) => (
            <VersusCard
              key={vc.id}
              challenge={vc}
              onAccept={handleAcceptVersus}
              onDecline={handleDeclineVersus}
              onViewProof={(id) => openPreviewProof(id, vc.title)}
              onEdit={(vc) =>
                openEditChallenge({
                  id: vc.id,
                  title: vc.title,
                  description: vc.description,
                  category: vc.category,
                  base_xp: vc.xp_reward,
                  proof_type: vc.proof_type,
                })
              }
            />
          ))}
        </div>
      </div>

      {/* Add Routine Modal */}
      {showRoutineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-brand-edge bg-brand-surface p-6">
            <h2 className="text-xl font-bold text-brand-accent">Add Daily Routine</h2>
            <form className="mt-6 space-y-4" onSubmit={handleCreateRoutine}>
              <input
                type="text"
                required
                value={routineTitle}
                onChange={(e) => setRoutineTitle(e.target.value)}
                placeholder="e.g. 30-min workout"
                className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-accent focus:outline-none"
              />
              <select
                value={routineCategory}
                onChange={(e) => setRoutineCategory(e.target.value)}
                className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-accent focus:outline-none"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c.charAt(0).toUpperCase() + c.slice(1)}
                  </option>
                ))}
              </select>
              <div className="grid grid-cols-2 gap-4">
                <select
                  value={routineXp}
                  onChange={(e) => setRoutineXp(Number(e.target.value))}
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-accent focus:outline-none"
                >
                  <option value={10}>Easy (+10 XP)</option>
                  <option value={25}>Medium (+25 XP)</option>
                  <option value={50}>Hard (+50 XP)</option>
                </select>
                <input
                  type="time"
                  value={routineTime}
                  onChange={(e) => setRoutineTime(e.target.value)}
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-accent focus:outline-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRoutineModal(false)}
                  className="flex-1 rounded-lg border border-brand-edge-strong px-4 py-3 text-sm font-medium text-slate-300 hover:border-slate-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={routineBusy}
                  className="flex-1 rounded-lg bg-brand-action px-4 py-3 font-bold text-white transition hover:bg-brand-action-dark disabled:opacity-60"
                >
                  {routineBusy ? "Adding…" : "Add Routine"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Challenge Modal */}
      {showChallengeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-brand-edge bg-brand-surface p-6">
            <h2 className="text-xl font-bold text-brand-action">Create Daily Challenge</h2>
            <form className="mt-6 space-y-4" onSubmit={handleCreateChallenge}>
              <input
                type="text"
                required
                value={challengeTitle}
                onChange={(e) => setChallengeTitle(e.target.value)}
                placeholder="e.g. 30-min run"
                className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-action focus:outline-none"
              />
              <textarea
                value={challengeDesc}
                onChange={(e) => setChallengeDesc(e.target.value)}
                rows={3}
                placeholder="What should participants do?"
                className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-action focus:outline-none"
              />
              <div className="grid grid-cols-2 gap-4">
                <select
                  value={challengeCategory}
                  onChange={(e) => setChallengeCategory(e.target.value)}
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c.charAt(0).toUpperCase() + c.slice(1)}
                    </option>
                  ))}
                </select>
                <select
                  value={challengeXp}
                  onChange={(e) => setChallengeXp(Number(e.target.value))}
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                >
                  <option value={20}>Easy (+20 XP)</option>
                  <option value={40}>Medium (+40 XP)</option>
                  <option value={70}>Hard (+70 XP)</option>
                  <option value={100}>Expert (+100 XP)</option>
                </select>
              </div>
              <select
                value={challengeProof}
                onChange={(e) => setChallengeProof(e.target.value)}
                className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
              >
                {PROOF_TYPES.map((p) => (
                  <option key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </option>
                ))}
              </select>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowChallengeModal(false)}
                  className="flex-1 rounded-lg border border-brand-edge-strong px-4 py-3 text-sm font-medium text-slate-300 hover:border-slate-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={challengeBusy}
                  className="flex-1 rounded-lg bg-brand-action px-4 py-3 font-bold text-white transition hover:bg-brand-action-dark disabled:opacity-60"
                >
                  {challengeBusy ? "Creating…" : "Create Challenge"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Challenge Modal */}
      {editingChallenge && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-brand-action bg-brand-surface p-6">
            <h2 className="text-xl font-bold text-brand-action">Edit Challenge</h2>
            <p className="mt-1 text-xs text-slate-500">
              {editingChallenge.title} · only you can change this
            </p>
            <form className="mt-6 space-y-4" onSubmit={handleSaveChallengeEdit}>
              <div>
                <label className="text-[10px] uppercase text-slate-500">Title</label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-action focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[10px] uppercase text-slate-500">Description</label>
                <textarea
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  rows={3}
                  placeholder="What should participants do?"
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-action focus:outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase text-slate-500">Category</label>
                  <select
                    value={editCategory}
                    onChange={(e) => setEditCategory(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c.charAt(0).toUpperCase() + c.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-500">Difficulty</label>
                  <select
                    value={editDifficulty}
                    onChange={(e) => setEditDifficulty(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                  >
                    {["easy", "medium", "hard", "expert"].map((d) => (
                      <option key={d} value={d}>
                        {d.charAt(0).toUpperCase() + d.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase text-slate-500">XP reward</label>
                  <input
                    type="number"
                    min={0}
                    value={editXp}
                    onChange={(e) => setEditXp(Number(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase text-slate-500">Proof type</label>
                  <select
                    value={editProof}
                    onChange={(e) => setEditProof(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                  >
                    {PROOF_TYPES.map((p) => (
                      <option key={p} value={p}>
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingChallenge(null)}
                  className="flex-1 rounded-lg border border-brand-edge-strong px-4 py-3 text-sm font-medium text-slate-300 hover:border-slate-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editBusy}
                  className="flex-1 rounded-lg bg-brand-action px-4 py-3 font-bold text-white transition hover:bg-brand-action-dark disabled:opacity-60"
                >
                  {editBusy ? "Saving…" : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Challenge a Rival Modal */}
      {showRivalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-brand-action bg-brand-surface p-6">
            <h2 className="text-xl font-bold text-brand-action">⚔️ Challenge a Rival</h2>
            <form className="mt-6 space-y-4" onSubmit={handleCreateRivalChallenge}>
              <select
                value={rivalTarget}
                onChange={(e) => setRivalTarget(e.target.value)}
                className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
              >
                <option value="rival2">rival2</option>
                <option value="higuys">higuys</option>
                <option value="unitygamers143">unitygamers143</option>
              </select>
              <input
                type="text"
                required
                value={rivalTitle}
                onChange={(e) => setRivalTitle(e.target.value)}
                placeholder="e.g. Morning Sprint"
                className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-action focus:outline-none"
              />
              <div className="grid grid-cols-2 gap-4">
                <select
                  value={rivalProof}
                  onChange={(e) => setRivalProof(e.target.value)}
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                >
                  <option value="photo">Photo</option>
                  <option value="text">Text</option>
                  <option value="link">Link</option>
                </select>
                <select
                  value={rivalXp}
                  onChange={(e) => setRivalXp(Number(e.target.value))}
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white focus:border-brand-action focus:outline-none"
                >
                  <option value={50}>+50 XP</option>
                  <option value={100}>+100 XP</option>
                  <option value={200}>+200 XP</option>
                  <option value={500}>+500 XP</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRivalModal(false)}
                  className="flex-1 rounded-lg border border-brand-edge-strong px-4 py-3 text-sm font-medium text-slate-300 hover:border-slate-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={rivalBusy}
                  className="flex-1 rounded-lg bg-brand-action px-4 py-3 font-extrabold text-white transition hover:bg-brand-action-dark disabled:opacity-60"
                >
                  {rivalBusy ? "Sending…" : "⚔️ Send Challenge"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Submit Proof Modal */}
      {showProofModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-brand-edge bg-brand-surface p-6">
            <h2 className="text-xl font-bold text-brand-accent">Submit Proof</h2>
            <p className="text-xs text-slate-500">{proofChallengeTitle}</p>
            <form className="mt-6 space-y-4" onSubmit={handleSubmitProof}>
              <div className="flex gap-2">
                {(["photo", "text", "link"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setProofType(t)}
                    className={`flex-1 rounded-lg border px-3 py-2 text-xs font-bold transition ${
                      proofType === t
                        ? "border-brand-action bg-brand-action/20 text-white"
                        : "border-brand-edge text-slate-400 hover:border-brand-edge-strong"
                    }`}
                  >
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
              {proofType === "photo" && (
                <>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleProofFileChange}
                    className="w-full text-xs text-slate-400 file:mr-3 file:rounded-md file:border file:border-brand-edge file:bg-brand-base file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-300"
                  />
                  {proofFileDataUrl && (
                    <img
                      src={proofFileDataUrl}
                      alt="proof preview"
                      className="max-h-48 w-full rounded-lg border border-brand-edge object-contain bg-black/40"
                    />
                  )}
                  <input
                    type="text"
                    value={proofUrl}
                    onChange={(e) => setProofUrl(e.target.value)}
                    placeholder="Or paste image URL"
                    className="w-full rounded-lg border border-brand-edge bg-brand-base px-3 py-2 text-white placeholder-slate-600 focus:border-brand-accent focus:outline-none"
                  />
                </>
              )}
              {proofType === "text" && (
                <textarea
                  required
                  rows={4}
                  value={proofText}
                  onChange={(e) => setProofText(e.target.value)}
                  placeholder="e.g. 100 push-ups in 4 sets"
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-4 py-3 text-white placeholder-slate-600 focus:border-brand-accent focus:outline-none"
                />
              )}
              {proofType === "link" && (
                <input
                  type="text"
                  required
                  value={proofUrl}
                  onChange={(e) => setProofUrl(e.target.value)}
                  placeholder="https://strava.com/activities/..."
                  className="w-full rounded-lg border border-brand-edge bg-brand-base px-3 py-2 text-white placeholder-slate-600 focus:border-brand-accent focus:outline-none"
                />
              )}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowProofModal(false)}
                  className="flex-1 rounded-lg border border-brand-edge-strong px-4 py-3 text-sm font-medium text-slate-300 hover:border-slate-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitProofBusy}
                  className="flex-1 rounded-lg bg-brand-action px-4 py-3 font-bold text-white transition hover:bg-brand-action-dark disabled:opacity-60"
                >
                  {submitProofBusy ? "Submitting…" : "Submit Proof"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Proof Preview Modal */}
      {showPreviewModal && previewChallengeId && (
        <ProofPreviewModal
          challengeId={previewChallengeId}
          challengeTitle={previewChallengeTitle}
          onClose={() => setShowPreviewModal(false)}
          onApproved={() => {
            setMessage("Proof reviewed!");
            refreshChallenges();
            refreshProfile();
          }}
        />
      )}
    </div>
  );
}

function computeLevel(xp: number): number {
  if (xp <= 0) return 1;
  return Math.max(1, Math.floor(Math.pow(xp / 100, 1 / 1.5)) + 1);
}

/**
 * Mirrors backend app.modules.game.service.calculate_level_and_progress.
 * 0 XP -> level 1 -> 0 / 283 XP -> an empty 0% bar.
 */
function computeProgress(xp: number, level: number) {
  if (xp <= 0) return { currentLevelXP: 0, nextLevelXP: 283, progressPercent: 0 };
  const xpForLevel = (l: number) => Math.floor(100 * Math.pow(l, 1.5));
  const prev = xpForLevel(level - 1);
  const next = xpForLevel(level);
  const span = Math.max(next - prev, 1);
  const lvlXp = Math.max(0, xp - prev);
  const progressPercent = Math.max(0, Math.min(100, (lvlXp / span) * 100));
  return { currentLevelXP: lvlXp, nextLevelXP: span, progressPercent };
}

/** Prefer the server's canonical numbers so the bar never disagrees with the API. */
function resolveProgress(profile: ProfileData | null, xp: number, level: number) {
  const serverPercent = profile?.progress_percent;
  const serverInLevel = profile?.xp_in_level;
  const serverSpan = profile?.level_xp_span;
  if (
    serverPercent !== undefined &&
    serverInLevel !== undefined &&
    serverSpan !== undefined
  ) {
    return {
      currentLevelXP: serverInLevel,
      nextLevelXP: serverSpan,
      progressPercent: serverPercent,
    };
  }
  return computeProgress(xp, level);
}

function getBmiBadge(bmi: number | null): string {
  if (bmi === null) return "Unknown";
  if (bmi < 18.5) return "Under";
  if (bmi < 25) return "Normal";
  if (bmi < 30) return "Athletic";
  return "High";
}
