import { useState } from "react";

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

interface VersusCardProps {
  challenge: VersusChallenge;
  onAccept: (id: string) => void;
  onDecline: (id: string) => void;
  onViewProof: (challengeId: string) => void;
  onEdit?: (challenge: VersusChallenge) => void;
}

export default function VersusCard({
  challenge,
  onAccept,
  onDecline,
  onViewProof,
  onEdit,
}: VersusCardProps) {
  const [busy, setBusy] = useState(false);

  const isPending = challenge.status === "PENDING_ACCEPTANCE";
  const isChallenger = challenge.is_challenger;
  const isActive = challenge.status === "ACTIVE";

  const handleAccept = async () => {
    setBusy(true);
    onAccept?.(challenge.id);
    setBusy(false);
  };

  return (
    <div className="rounded-2xl border border-brand-action bg-brand-surface p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full border border-brand-action bg-brand-action text-lg font-extrabold text-white">
            {challenge.opponent_username?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Rival vs You</p>
            <h3 className="font-bold text-white">{challenge.title}</h3>
          </div>
        </div>
        <div className="text-right">
          <span className="rounded-full bg-brand-accent/15 px-3 py-1 text-xs font-bold text-brand-accent">
            +{challenge.xp_reward} XP
          </span>
          <p className="mt-1 text-xs text-slate-500">{challenge.category}</p>
        </div>
      </div>

      {challenge.description && <p className="mt-3 text-sm text-slate-400">{challenge.description}</p>}

      <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
        <span className="rounded-full bg-brand-edge px-2 py-0.5">{challenge.proof_type} proof</span>
        <span>vs {challenge.opponent_username}</span>
      </div>

      <div className="mt-4 flex gap-2">
        {isPending && !isChallenger && (
          <>
            <button
              onClick={handleAccept}
              disabled={busy}
              className="flex-1 rounded-lg bg-brand-action px-4 py-2 text-xs font-bold text-white transition hover:bg-brand-action-dark disabled:opacity-60"
            >
              {busy ? "Accepting…" : "Accept"}
            </button>
            <button
              onClick={() => onDecline?.(challenge.id)}
              disabled={busy}
              className="flex-1 rounded-lg border border-brand-edge-strong px-4 py-2 text-xs font-bold text-slate-300 transition hover:border-red-500/60 hover:text-red-300 disabled:opacity-60"
            >
              Decline
            </button>
          </>
        )}
        {isPending && isChallenger && (
          <p className="flex-1 text-center text-xs text-slate-400">
            Waiting for {challenge.opponent_username} to accept…
          </p>
        )}
        {isActive && (
          <button
            onClick={() => onViewProof?.(challenge.id)}
            className="flex-1 rounded-lg bg-brand-action px-4 py-2 text-xs font-bold text-white transition hover:bg-brand-action-dark"
          >
            View Rival&apos;s Proof
          </button>
        )}
        {challenge.status === "DECLINED" && (
          <p className="flex-1 text-center text-xs text-slate-500">Challenge declined.</p>
        )}
        {isChallenger && onEdit && (
          <button
            onClick={() => onEdit(challenge)}
            aria-label={`Edit ${challenge.title}`}
            className="rounded-lg border border-brand-action px-3 py-2 text-xs font-bold text-brand-action transition hover:bg-brand-action/10"
          >
            Edit
          </button>
        )}
      </div>
    </div>
  );
}
