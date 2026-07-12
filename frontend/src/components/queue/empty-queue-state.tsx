import type { JSX } from "react";
import { Music2 } from "lucide-react";

export function EmptyQueueState(): JSX.Element {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center rounded-[28px] border border-dashed border-white/8 bg-white/[0.025] px-6 py-10 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-3xl bg-white/6">
        <Music2 className="h-6 w-6 text-slate-300" />
      </div>
      <h3 className="text-xl font-medium text-white">Queue is empty</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
        Add the first song below to start the room. The shared queue remains the visual
        center of the experience.
      </p>
    </div>
  );
}
