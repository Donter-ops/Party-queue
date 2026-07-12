import type { JSX } from "react";
import { Radio } from "lucide-react";

export function BrandMark(): JSX.Element {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-slate-950 shadow-[0_10px_30px_rgba(255,255,255,0.16)]">
        <Radio className="h-5 w-5" />
      </div>
      <div>
        <p className="text-sm font-semibold tracking-[0.22em] text-slate-500">PARTYQUEUE</p>
        <p className="text-lg font-semibold text-white">Shared music, simplified.</p>
      </div>
    </div>
  );
}
