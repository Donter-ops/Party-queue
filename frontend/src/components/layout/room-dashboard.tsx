import { Copy, LogOut, RefreshCw } from "lucide-react";
import { useMemo, type JSX } from "react";

import type { CreateSongPayload, RoomDetail } from "../../types";
import { AddSongForm } from "../forms/add-song-form";
import { QueueList } from "../queue/queue-list";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { AgentNotification } from "../ui/notification";

interface RoomDashboardProps {
  errorMessage: string | null;
  isRefreshing: boolean;
  room: RoomDetail;
  roomShareUrl: string;
  savedGuestName: string;
  onAddSong: (payload: CreateSongPayload) => Promise<void>;
  onCopyShareLink: () => Promise<void>;
  onDeleteSong: (songId: string) => Promise<void>;
  onLeaveRoom: () => void;
  onMoveSong: (songId: string, nextPosition: number) => Promise<void>;
  onRefreshRoom: () => Promise<void>;
}

export function RoomDashboard({
  errorMessage,
  isRefreshing,
  room,
  roomShareUrl,
  savedGuestName,
  onAddSong,
  onCopyShareLink,
  onDeleteSong,
  onLeaveRoom,
  onMoveSong,
  onRefreshRoom,
}: RoomDashboardProps): JSX.Element {
  const sortedSongs = useMemo(
    () => [...room.songs].sort((leftSong, rightSong) => leftSong.position - rightSong.position),
    [room.songs],
  );

  const memberCount = useMemo(
    () => new Set(sortedSongs.map((song) => song.added_by.trim()).filter(Boolean)).size,
    [sortedSongs],
  );

  return (
    <section className="space-y-8">
      <Card className="overflow-hidden">
        <CardContent className="space-y-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
                  Listening together
                </p>
                <h1 className="text-3xl font-semibold text-white">
                  {room.name}
                </h1>
                <p className="text-sm text-slate-400">
                  {memberCount} member{memberCount !== 1 ? "s" : ""}
                </p>
              </div>

              {/* Hidden by default so future agent signals can surface without changing the main layout. */}
              <AgentNotification message="✨ Matching song..." visible={false} />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button
                className="gap-2"
                onClick={() => {
                  void onCopyShareLink();
                }}
                variant="outline"
              >
                <Copy className="h-4 w-4" />
                Copy room link
              </Button>
              <Button className="gap-2" onClick={onLeaveRoom} variant="ghost">
                <LogOut className="h-4 w-4" />
                Leave room
              </Button>
            </div>
          </div>

<Card className="border-white/5">
  <CardContent className="space-y-3">
    <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
      Now Playing
    </p>

    {sortedSongs.length > 0 ? (
      <>
        <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white">
          {sortedSongs[0].title}
        </h2>

        <p className="text-lg text-slate-300">
          {sortedSongs[0].artist}
        </p>

        <p className="text-sm text-slate-500">
          Added by {sortedSongs[0].added_by}
        </p>
      </>
    ) : (
      <>
        <h2 className="text-2xl font-semibold text-white">
          Nothing playing
        </h2>

        <p className="text-slate-400">
          Add the first song to start the session.
        </p>
      </>
    )}
  </CardContent>
</Card>

          {errorMessage ? (
            <p className="rounded-2xl border border-rose-400/12 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {errorMessage}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-8">
        <Card>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
                Shared queue
              </p>
              <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white">
                Queue
              </h2>
              <p className="text-sm text-slate-400">
               Songs are played in the order below.
              </p>
            </div>
            <QueueList onDeleteSong={onDeleteSong} onMoveSong={onMoveSong} songs={sortedSongs} />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
                Add song
              </p>
<h2 className="text-3xl font-semibold tracking-[-0.04em] text-white">
    Add Song
</h2>
<p className="text-sm text-slate-400">
    Search or add a song to the shared queue.
</p>
            </div>
            <AddSongForm initialGuestName={savedGuestName} onSubmit={onAddSong} />
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="rounded-[24px] border border-white/6 bg-black/20 p-5">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-3 truncate text-lg font-medium text-slate-100">{value}</p>
    </div>
  );
}
