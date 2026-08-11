import type { JSX } from "react";

import type { Song } from "../../types";
import { Card, CardContent } from "../ui/card";
import { QueueList } from "./queue-list";

interface QueueSectionProps {
  onDeleteSong: (songId: string) => Promise<void>;
  onMoveSong: (songId: string, nextPosition: number) => Promise<void>;
  songs: Song[];
}

export function QueueSection({
  onDeleteSong,
  onMoveSong,
  songs,
}: QueueSectionProps): JSX.Element {
  return (
    <Card>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
            Shared queue
          </p>
          <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white">Queue</h2>
          <p className="text-sm text-slate-400">Songs are played in the order below.</p>
        </div>
        <QueueList onDeleteSong={onDeleteSong} onMoveSong={onMoveSong} songs={songs} />
      </CardContent>
    </Card>
  );
}
