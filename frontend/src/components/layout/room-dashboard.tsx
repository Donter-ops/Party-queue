import { useMemo, type JSX } from "react";

import type {
  CreateSongPayload,
  PlaybackSession,
  ResolverDebugTrace,
  RoomDetail,
} from "../../types";
import { AddSongForm } from "../forms/add-song-form";
import { RoomHeader } from "./room-header";
import { PlaybackPanel } from "../playback/playback-panel";
import { QueueSection } from "../queue/queue-section";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";

interface RoomDashboardProps {
  errorMessage: string | null;
  isRefreshing: boolean;
  playbackSession: PlaybackSession | null;
  resolverDebugTrace: ResolverDebugTrace | null;
  room: RoomDetail;
  roomShareUrl: string;
  savedGuestName: string;
  onAddSong: (payload: CreateSongPayload) => Promise<void>;
  onCopyShareLink: () => Promise<void>;
  onDeleteSong: (songId: string) => Promise<void>;
  onLeaveRoom: () => void;
  onMoveSong: (songId: string, nextPosition: number) => Promise<void>;
  onPlaybackFinished: () => Promise<void>;
  onPlaybackNext: () => Promise<void>;
  onPlaybackPrevious: () => Promise<void>;
  onPlaybackToggle: () => Promise<void>;
}

export function RoomDashboard({
  errorMessage,
  isRefreshing,
  playbackSession,
  resolverDebugTrace,
  room,
  roomShareUrl,
  savedGuestName,
  onAddSong,
  onCopyShareLink,
  onDeleteSong,
  onLeaveRoom,
  onMoveSong,
  onPlaybackFinished,
  onPlaybackNext,
  onPlaybackPrevious,
  onPlaybackToggle,
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
          <RoomHeader
            isRefreshing={isRefreshing}
            memberCount={memberCount}
            onCopyShareLink={onCopyShareLink}
            onLeaveRoom={onLeaveRoom}
            roomName={room.name}
          />

          <PlaybackPanel
            onPlaybackFinished={onPlaybackFinished}
            onPlaybackNext={onPlaybackNext}
            onPlaybackPrevious={onPlaybackPrevious}
            onPlaybackToggle={onPlaybackToggle}
            playbackSession={playbackSession}
            resolverDebugTrace={resolverDebugTrace}
            sortedSongs={sortedSongs}
          />

          {errorMessage ? (
            <p className="rounded-2xl border border-rose-400/12 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {errorMessage}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.9fr)] xl:items-start">
        <QueueSection onDeleteSong={onDeleteSong} onMoveSong={onMoveSong} songs={sortedSongs} />
        <Card>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
                Add song
              </p>
              <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white">Add Song</h2>
              <p className="text-sm text-slate-400">Search or add a song to the shared queue.</p>
            </div>
            <AddSongForm initialGuestName={savedGuestName} onSubmit={onAddSong} />
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
