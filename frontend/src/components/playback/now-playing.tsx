import type { JSX } from "react";

interface NowPlayingProps {
  artist: string | null;
  provider: string | null;
  title: string | null;
}

export function NowPlaying({
  artist,
  provider,
  title,
}: NowPlayingProps): JSX.Element {
  return (
    <section className="rounded-[28px] border border-white/6 bg-white/[0.035] p-6 shadow-[0_20px_80px_rgba(15,23,42,0.18)]">
      <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
        Now Playing
      </p>

      {title ? (
        <div className="mt-4 space-y-2">
          <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl">
            {title}
          </h2>
          <p className="text-base text-slate-300 sm:text-lg">{artist}</p>
          <p className="text-sm uppercase tracking-[0.18em] text-slate-500">
            {provider ?? "unknown"}
          </p>
        </div>
      ) : (
        <div className="mt-4 space-y-2">
          <h2 className="text-2xl font-semibold text-white">No song playing</h2>
          <p className="text-sm text-slate-400 sm:text-base">
            Press Play when the queue is ready.
          </p>
        </div>
      )}
    </section>
  );
}
