import { useState, type JSX } from "react";

import type { Song } from "../../types";
import { EmptyQueueState } from "./empty-queue-state";
import { QueueCard } from "./queue-card";

interface QueueListProps {
  songs: Song[];
  onDeleteSong: (songId: string) => Promise<void>;
  onMoveSong: (songId: string, nextPosition: number) => Promise<void>;
}

export function QueueList({
  songs,
  onDeleteSong,
  onMoveSong,
}: QueueListProps): JSX.Element {
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
    return <EmptyQueueState />;
  }

  return (
    <div className="space-y-4">
      {sortedSongs.map((song, index) => (
        <QueueCard
          canMoveDown={index < sortedSongs.length - 1}
          canMoveUp={index > 0}
          isBusy={busySongId === song.id}
          key={song.id}
          onDelete={() => {
            void handleDelete(song.id);
          }}
          onMoveDown={() => {
            void handleMove(song.id, song.position + 1);
          }}
          onMoveUp={() => {
            void handleMove(song.id, song.position - 1);
          }}
          song={song}
        />
      ))}
    </div>
  );
}
