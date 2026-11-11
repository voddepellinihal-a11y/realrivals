export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  level: number;
  xp: number;
  streak: number;
}

interface LeaderboardCardProps {
  entries: LeaderboardEntry[];
  currentUserId?: string | null;
  loading?: boolean;
}

export default function LeaderboardCard({
  entries,
  currentUserId,
  loading,
}: LeaderboardCardProps) {
  return (
    <div className="rounded-2xl border border-brand-edge bg-brand-surface p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-xl font-bold text-brand-accent">Leaderboard</h2>
        <p className="text-[10px] uppercase tracking-widest text-slate-500">
          Ranked by lifetime XP
        </p>
      </div>

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading standings…</p>
      ) : entries.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No ranked players yet — finish a routine to claim the top spot.
        </p>
      ) : (
        <ol className="mt-4 border-t border-brand-edge">
          {entries.map((entry) => {
            const isMe = entry.user_id === currentUserId;
            return (
              <li
                key={entry.user_id}
                className={`flex items-center gap-3 border-b border-brand-edge py-2.5 last:border-b-0 ${
                  isMe ? "bg-brand-accent/5" : ""
                }`}
              >
                <span
                  className={`w-6 shrink-0 text-center font-mono text-xs ${
                    entry.rank === 1 ? "text-brand-accent" : "text-slate-500"
                  }`}
                >
                  {entry.rank}
                </span>
                <span
                  className={`flex-1 truncate text-sm ${
                    isMe ? "font-semibold text-white" : "font-medium text-slate-200"
                  }`}
                >
                  {entry.username}
                  {isMe && <span className="ml-2 text-[10px] uppercase text-slate-500">you</span>}
                </span>
                {entry.streak > 0 && (
                  <span className="shrink-0 font-mono text-xs text-slate-500">
                    {entry.streak}d
                  </span>
                )}
                <span className="shrink-0 rounded-full bg-brand-edge px-2 py-0.5 text-[10px] font-bold uppercase text-slate-300">
                  Lv {entry.level}
                </span>
                <span className="w-20 shrink-0 text-right font-mono text-xs text-brand-accent">
                  {entry.xp} XP
                </span>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
