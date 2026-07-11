import { useState } from "react";
import type { JSX } from "react";

import type { Song } from "../App";

interface SongListProps {
  songs: Song[];
  onDeleteSong: (songId: string) => Promise<void>;
  onMoveSong: (songId: string, nextPosition: number) => Promise<void>;
}

const sourceBadgeClassNames: Record<string, string> = {
  manual: "bg-vinyl text-white",
  spotify: "bg-[#1DB954] text-white",
  youtube_music: "bg-[#FF0033] text-white",
};

const sourceLabels: Record<string, string> = {
  manual: "Manuell",
  spotify: "Spotify",
  youtube_music: "YouTube Music",
};

export function SongList({
  songs,
  onDeleteSong,
  onMoveSong,
}: SongListProps): JSX.Element {
  const [busySongId, setBusySongId] = useState<string | null>(null);

  const sortedSongs = [...songs].sort((leftSong, rightSong) => leftSong.position - rightSong.position);

  async function handleMove(songId: string, nextPosition: number): Promise<void> {
    try {
      setBusySongId(songId);
      await onMoveSong(songId, nextPosition);
    } finally {
      setBusySongId(null);
    }
  }

  async function handleDelete(songId: string): Promise<void> {
    try {
      setBusySongId(songId);
      await onDeleteSong(songId);
    } finally {
      setBusySongId(null);
    }
  }

  if (sortedSongs.length === 0) {
    return (
      <div className="rounded-[1.5rem] border border-dashed border-vinyl/15 bg-cream/70 px-6 py-10 text-center text-vinyl/55">
        Noch keine Songs in der Queue.
      </div>
    );
  }

  return (
    <ol className="space-y-3">
      {sortedSongs.map((song, index) => {
        const isBusy = busySongId === song.id;
        const sourceLabel = sourceLabels[song.source] ?? "Quelle";
        const sourceClassName = sourceBadgeClassNames[song.source] ?? "bg-vinyl text-white";

        return (
          <li
            key={song.id}
            className="flex flex-col gap-4 rounded-[1.5rem] border border-vinyl/8 bg-cream/65 px-5 py-4 md:flex-row md:items-center md:justify-between"
          >
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-vinyl text-sm font-bold text-white">
                {song.position + 1}
              </div>

              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="truncate text-lg font-semibold text-vinyl">{song.artist}</p>
                  <span className={`rounded-full px-3 py-1 text-xs font-bold ${sourceClassName}`}>
                    {sourceLabel}
                  </span>
                </div>
                <p className="truncate text-sm text-vinyl/68">{song.title}</p>
                <p className="mt-1 text-sm text-vinyl/55">eingereicht von {song.added_by}</p>
                {song.external_url ? (
                  <a
                    className="mt-2 inline-flex text-sm font-semibold text-coral transition hover:text-vinyl"
                    href={song.external_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Musik-Link öffnen
                  </a>
                ) : null}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                className="rounded-full border border-vinyl/10 bg-white px-4 py-2 text-sm font-semibold text-vinyl transition hover:border-vinyl hover:bg-vinyl hover:text-white disabled:cursor-not-allowed disabled:opacity-45"
                disabled={isBusy || index === 0}
                onClick={() => {
                  void handleMove(song.id, song.position - 1);
                }}
                type="button"
              >
                Nach oben
              </button>
              <button
                className="rounded-full border border-vinyl/10 bg-white px-4 py-2 text-sm font-semibold text-vinyl transition hover:border-vinyl hover:bg-vinyl hover:text-white disabled:cursor-not-allowed disabled:opacity-45"
                disabled={isBusy || index === sortedSongs.length - 1}
                onClick={() => {
                  void handleMove(song.id, song.position + 1);
                }}
                type="button"
              >
                Nach unten
              </button>
              <button
                className="rounded-full border border-coral/18 bg-coral/10 px-4 py-2 text-sm font-semibold text-coral transition hover:bg-coral hover:text-white disabled:cursor-not-allowed disabled:opacity-45"
                disabled={isBusy}
                onClick={() => {
                  void handleDelete(song.id);
                }}
                type="button"
              >
                {isBusy ? "..." : "Entfernen"}
              </button>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
