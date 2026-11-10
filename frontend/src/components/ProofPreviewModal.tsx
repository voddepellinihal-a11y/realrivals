import { useEffect, useState } from "react";

interface Submission {
  id: string;
  challenge_id: string;
  user_id: string;
  username: string;
  proof_url: string;
  proof_text: string | null;
  proof_type: string;
  description: string;
  status: string;
  submitted_at: string | null;
  is_me: boolean;
}

interface ProofPreviewModalProps {
  challengeId: string;
  challengeTitle?: string;
  onClose: () => void;
  onApproved?: () => void;
}

const statusCls = (status: string) => {
  switch (status) {
    case "PENDING_REVIEW":
      return "bg-brand-accent/15 text-brand-accent";
    case "approved":
    case "APPROVED":
      return "bg-brand-action/20 text-brand-action";
    default:
      return "bg-brand-edge text-slate-300";
  }
};

export default function ProofPreviewModal({
  challengeId,
  challengeTitle,
  onClose,
  onApproved,
}: ProofPreviewModalProps) {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionBusy, setActionBusy] = useState<string | null>(null);

  const api = async (path: string, body?: unknown, method?: string) => {
    const res = await fetch(path, {
      method: method ?? (body ? "POST" : "GET"),
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error((data as { detail?: string }).detail || `Request failed (${res.status})`);
    return data;
  };

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api(`/submissions/challenge/${challengeId}/submissions`);
      setSubmissions(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load submissions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [challengeId]);

  const review = async (submissionId: string, decision: "approved" | "rejected") => {
    setActionBusy(`${submissionId}-${decision}`);
    try {
      await api(`/submissions/${submissionId}/reviews`, { decision });
      onApproved?.();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed");
    } finally {
      setActionBusy(null);
    }
  };

  const rivalSubmissions = submissions.filter((s) => !s.is_me);
  const mySubmissions = submissions.filter((s) => s.is_me);

  const renderProof = (s: Submission) => {
    if (s.proof_type === "photo" && s.proof_url) {
      // If it's a data URL (base64), show it as an image.
      const isDataUrl = s.proof_url.startsWith("data:");
      if (isDataUrl) {
        return (
          <img
            src={s.proof_url}
            alt="proof"
            className="max-h-80 w-full rounded-lg border border-brand-edge object-contain bg-black/40"
          />
        );
      }
      return (
        <a
          className="text-brand-accent underline"
          href={s.proof_url}
          target="_blank"
          rel="noreferrer"
        >
          Open proof photo
        </a>
      );
    }
    if (s.proof_type === "link" && s.proof_url) {
      return (
        <a
          className="break-all text-brand-accent underline"
          href={s.proof_url}
          target="_blank"
          rel="noreferrer"
        >
          {s.proof_url}
        </a>
      );
    }
    if (s.proof_type === "text" && s.proof_text) {
      return (
        <pre className="whitespace-pre-wrap rounded-lg border border-brand-edge bg-brand-base p-3 text-sm text-slate-100">
          {s.proof_text}
        </pre>
      );
    }
    return <p className="text-sm text-slate-400">No proof submitted yet.</p>;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-brand-edge bg-brand-surface p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-brand-accent">Proof of Work</h2>
            <p className="text-xs text-slate-400">{challengeTitle ?? challengeId}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg border border-brand-edge px-3 py-2 text-sm text-slate-300 transition hover:border-brand-action hover:text-white"
          >
            Close
          </button>
        </div>

        {error && (
          <p className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        )}
        {loading && <p className="mt-4 text-slate-400">Loading proofs…</p>}

        {!loading && (
          <div className="mt-5 space-y-6">
            <section>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-brand-accent">
                Your Submission
              </h3>
              {mySubmissions.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">You haven't submitted proof yet.</p>
              ) : (
                mySubmissions.map((s) => (
                  <div
                    key={s.id}
                    className="mt-3 rounded-xl border border-brand-edge bg-brand-base p-4"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500">{s.username}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${statusCls(s.status)}`}>
                        {s.status}
                      </span>
                    </div>
                    <div className="mt-2">{renderProof(s)}</div>
                  </div>
                ))
              )}
            </section>

            <section>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-brand-action">
                Rival&apos;s Proof
              </h3>
              {rivalSubmissions.length === 0 ? (
                <p className="mt-2 text-sm text-slate-500">Rival hasn't submitted proof yet.</p>
              ) : (
                rivalSubmissions.map((s) => (
                  <div
                    key={s.id}
                    className="mt-3 rounded-xl border border-brand-action/40 bg-brand-base p-4"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500">{s.username}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${statusCls(s.status)}`}>
                        {s.status}
                      </span>
                    </div>
                    <div className="mt-2">{renderProof(s)}</div>
                    {s.status === "PENDING_REVIEW" && (
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => review(s.id, "approved")}
                          disabled={actionBusy !== null}
                          className="flex-1 rounded-lg bg-brand-accent px-3 py-2 text-xs font-bold text-brand-base transition hover:bg-brand-accent-soft disabled:opacity-60"
                        >
                          ✅ Approve (+XP)
                        </button>
                        <button
                          onClick={() => review(s.id, "rejected")}
                          disabled={actionBusy !== null}
                          className="flex-1 rounded-lg border border-red-500/40 px-3 py-2 text-xs font-bold text-red-300 transition hover:bg-red-500/10 disabled:opacity-60"
                        >
                          ❌ Reject
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
