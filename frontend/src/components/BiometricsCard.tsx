import type { FormEvent } from "react";

interface BiometricsCardProps {
  height: string;
  weight: string;
  targetWeight: string;
  onHeightChange: (value: string) => void;
  onWeightChange: (value: string) => void;
  onTargetWeightChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  busy: boolean;
  bmi: number | null;
  bmiBadge: string;
  heightCm: number | null;
  weightKg: number | null;
  targetWeightKg: number | null;
  weightDelta: number | null;
}

const inputCls =
  "mt-1.5 w-full rounded-lg border border-brand-edge bg-brand-base px-3 py-2 text-sm text-white placeholder-slate-600 focus:border-brand-accent focus:outline-none";

export default function BiometricsCard({
  height,
  weight,
  targetWeight,
  onHeightChange,
  onWeightChange,
  onTargetWeightChange,
  onSubmit,
  busy,
  bmi,
  bmiBadge,
  heightCm,
  weightKg,
  targetWeightKg,
  weightDelta,
}: BiometricsCardProps) {
  return (
    <div className="rounded-2xl border border-brand-edge bg-brand-surface p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-bold text-white">Personal Biometrics</h2>
        <p className="text-[10px] uppercase tracking-widest text-slate-500">
          Height · Weight · Target · BMI (live)
        </p>
      </div>

      <p className="mt-1.5 text-xs text-slate-400">
        {heightCm !== null && weightKg !== null && targetWeightKg !== null ? (
          <>
            Currently <span className="font-semibold text-white">{weightKg} kg</span> at{" "}
            <span className="font-semibold text-white">{heightCm} cm</span> — target{" "}
            <span className="font-semibold text-brand-accent">{targetWeightKg} kg</span>
            {weightDelta !== null && weightDelta !== 0 && (
              <span className="text-slate-500">
                {" "}({weightDelta > 0 ? `${weightDelta} kg to gain` : `${Math.abs(weightDelta)} kg to lose`})
              </span>
            )}
          </>
        ) : (
          "Add your height, weight, and target to see your BMI and goal instantly."
        )}
      </p>

      <form onSubmit={onSubmit} className="mt-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <label htmlFor="biometric-height" className="text-[10px] uppercase tracking-wider text-slate-500">
              Height (cm)
            </label>
            <input
              id="biometric-height"
              type="number"
              min={0}
              value={height}
              onChange={(e) => onHeightChange(e.target.value)}
              placeholder="175"
              className={inputCls}
            />
          </div>
          <div>
            <label htmlFor="biometric-weight" className="text-[10px] uppercase tracking-wider text-slate-500">
              Weight (kg)
            </label>
            <input
              id="biometric-weight"
              type="number"
              min={0}
              value={weight}
              onChange={(e) => onWeightChange(e.target.value)}
              placeholder="72"
              className={inputCls}
            />
          </div>
          <div>
            <label htmlFor="biometric-target" className="text-[10px] uppercase tracking-wider text-slate-500">
              Target (kg)
            </label>
            <input
              id="biometric-target"
              type="number"
              min={0}
              value={targetWeight}
              onChange={(e) => onTargetWeightChange(e.target.value)}
              placeholder="70"
              className={inputCls}
            />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-brand-edge pt-4">
          <div className="flex items-center gap-3">
            <span className="text-[10px] uppercase tracking-widest text-slate-500">BMI</span>
            <span className="text-2xl font-extrabold tabular-nums text-brand-accent">{bmi ?? "—"}</span>
            <span className="rounded-full bg-brand-accent/15 px-2 py-0.5 text-[10px] font-bold uppercase text-brand-accent">
              {bmiBadge}
            </span>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg border border-brand-action/30 bg-brand-action px-5 py-2 font-medium text-sm text-white transition hover:bg-brand-action-dark disabled:opacity-60"
          >
            {busy ? "Saving…" : "Save Biometrics"}
          </button>
        </div>
      </form>
    </div>
  );
}
