import { Copy, LogOut, Pause, Play, SkipBack, SkipForward } from "lucide-react";
import { useEffect, useMemo, useRef, type JSX } from "react";

import type {
  CreateSongPayload,
  PlaybackSession,
  ResolverDebugTrace,
  RoomDetail,
} from "../../types";
import { AddSongForm } from "../forms/add-song-form";
import { YouTubePlayer, type YouTubePlayerHandle } from "../player/youtube-player";
import { QueueList } from "../queue/queue-list";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { AgentNotification } from "../ui/notification";

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
  const playerRef = useRef<YouTubePlayerHandle | null>(null);

  const currentSong = playbackSession?.current_song ?? null;
  const nextSong = playbackSession?.next_song ?? sortedSongs[0] ?? null;
  const shouldRenderYouTubePlayer =
    playbackSession?.provider_match?.provider === "youtube_music" &&
    Boolean(playbackSession.youtube_video_id);
  const currentProvider =
    playbackSession?.playable_provider ?? playbackSession?.provider_match?.provider ?? null;
  const isDevelopment =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

  const memberCount = useMemo(
    () => new Set(sortedSongs.map((song) => song.added_by.trim()).filter(Boolean)).size,
    [sortedSongs],
  );

  useEffect(() => {
    if (!shouldRenderYouTubePlayer || !playerRef.current) {
      return;
    }

    if (playbackSession?.state === "PAUSED") {
      playerRef.current.pause();
      return;
    }

    if (playbackSession?.state === "PLAYING") {
      playerRef.current.play();
    }
  }, [playbackSession?.state, shouldRenderYouTubePlayer]);

  const playbackButtonLabel =
    playbackSession?.state === "PLAYING"
      ? "Pause"
      : playbackSession?.state === "PAUSED"
        ? "Resume"
        : "Play";
  const playbackButtonIcon =
    playbackSession?.state === "PLAYING" ? (
      <Pause className="h-4 w-4" />
    ) : (
      <Play className="h-4 w-4 fill-current" />
    );
  const isPlaybackButtonDisabled =
    sortedSongs.length === 0 && playbackSession?.current_song == null;

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
                <h1 className="text-3xl font-semibold text-white">{room.name}</h1>
                <p className="text-sm text-slate-400">
                  {memberCount} member{memberCount !== 1 ? "s" : ""}
                  {isRefreshing ? " | syncing" : ""}
                </p>
              </div>

              {/* Hidden by default so future agent signals can surface without changing the main layout. */}
              <AgentNotification message="Matching song..." visible={false} />
            </div>

            <div className="flex flex-wrap gap-3">
              <div className="flex flex-wrap gap-3 rounded-full border border-white/8 bg-black/25 p-1.5 shadow-[0_18px_60px_rgba(15,23,42,0.22)]">
                <Button
                  className="gap-2 rounded-full"
                  disabled={!playbackSession?.previous_available}
                  onClick={() => {
                    void onPlaybackPrevious();
                  }}
                  variant="secondary"
                >
                  <SkipBack className="h-4 w-4" />
                  Previous
                </Button>
                <Button
                  className="gap-2 rounded-full"
                  disabled={isPlaybackButtonDisabled}
                  onClick={() => {
                    void onPlaybackToggle();
                  }}
                  variant="secondary"
                >
                  {playbackButtonIcon}
                  {playbackButtonLabel}
                </Button>
                <Button
                  className="gap-2 rounded-full"
                  disabled={isPlaybackButtonDisabled}
                  onClick={() => {
                    void onPlaybackNext();
                  }}
                  variant="secondary"
                >
                  <SkipForward className="h-4 w-4" />
                  Next
                </Button>
              </div>

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

              {currentSong ? (
                <>
                  <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white">
                    {currentSong.title}
                  </h2>
                  <p className="text-lg text-slate-300">{currentSong.artist}</p>
                  <p className="text-sm uppercase tracking-[0.18em] text-slate-500">
                    {currentProvider ?? currentSong.source}
                  </p>
                </>
              ) : (
                <>
                  <h2 className="text-2xl font-semibold text-white">No song playing</h2>
                  <p className="text-slate-400">Press Play when the queue is ready.</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="border-white/5">
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
                  Player
                </p>
                <h2 className="text-2xl font-semibold tracking-[-0.04em] text-white">
                  Shared Playback
                </h2>
              </div>

              {shouldRenderYouTubePlayer ? (
                <YouTubePlayer
                  ref={playerRef}
                  onEnded={() => {
                    void onPlaybackFinished();
                  }}
                  videoId={playbackSession?.youtube_video_id ?? null}
                />
              ) : (
                <div className="flex aspect-video min-h-[240px] items-center justify-center rounded-[28px] bg-black/30 px-6 text-center text-sm text-slate-400 shadow-[0_24px_80px_rgba(15,23,42,0.2)]">
                  Add a YouTube or YouTube Music link to play the video directly in the room.
                </div>
              )}

              {isDevelopment ? (
                <div className="space-y-3">
                  <div className="grid gap-3 rounded-[24px] border border-white/5 bg-black/20 p-5 md:grid-cols-2 xl:grid-cols-3">
                    <DebugItem label="Current Provider" value={playbackSession?.current_provider ?? "n/a"} />
                    <DebugItem label="Playable Provider" value={playbackSession?.playable_provider ?? "n/a"} />
                    <DebugItem label="Current Video ID" value={playbackSession?.youtube_video_id ?? "n/a"} />
                    <DebugItem
                      label="Queue Length"
                      value={String(playbackSession?.queue_length ?? sortedSongs.length)}
                    />
                    <DebugItem label="Current Song ID" value={playbackSession?.current_song_id ?? "n/a"} />
                    <DebugItem
                      label="Resolver Cache Hit"
                      value={playbackSession?.resolver_cache_hit ? "yes" : "no"}
                    />
                  </div>
                  <ResolverDebugPanel trace={resolverDebugTrace} />
                </div>
              ) : null}

              <div className="rounded-[24px] border border-white/5 bg-black/20 p-5">
                <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
                  Next Song
                </p>
                {nextSong ? (
                  <div className="mt-3 space-y-1">
                    <p className="text-xl font-semibold text-white">{nextSong.title}</p>
                    <p className="text-sm text-slate-300">{nextSong.artist}</p>
                    <p className="text-xs text-slate-500">Added by {nextSong.added_by}</p>
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-400">No next song queued yet.</p>
                )}
              </div>
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
              <h2 className="text-3xl font-semibold tracking-[-0.04em] text-white">Queue</h2>
              <p className="text-sm text-slate-400">Songs are played in the order below.</p>
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

function DebugItem({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="rounded-[24px] border border-white/6 bg-black/20 p-5">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-3 truncate text-lg font-medium text-slate-100">{value}</p>
    </div>
  );
}

function ResolverDebugPanel({ trace }: { trace: ResolverDebugTrace | null }): JSX.Element {
  return (
    <details className="rounded-[24px] border border-white/5 bg-black/20 p-5">
      <summary className="cursor-pointer list-none text-sm font-medium uppercase tracking-[0.22em] text-slate-400">
        Resolver Debug
      </summary>
      <div className="mt-4 space-y-5">
        {trace ? (
          <>
            <section className="space-y-2">
              <h3 className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">
                Spotify Metadata
              </h3>
              <div className="grid gap-3 md:grid-cols-2">
                <DebugItem label="Track ID" value={trace.spotify?.track_id ?? "n/a"} />
                <DebugItem label="Track Name" value={trace.spotify?.track_name ?? "n/a"} />
                <DebugItem label="Artists" value={trace.spotify?.artists.join(", ") || "n/a"} />
                <DebugItem label="Album" value={trace.spotify?.album ?? "n/a"} />
                <DebugItem
                  label="Duration (ms)"
                  value={trace.spotify?.duration_ms != null ? String(trace.spotify.duration_ms) : "n/a"}
                />
                <DebugItem label="ISRC" value={trace.spotify?.isrc ?? "n/a"} />
              </div>
            </section>

            <section className="space-y-2 rounded-[20px] border border-white/5 bg-white/[0.02] p-4">
              <h3 className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">
                Search Query
              </h3>
              <p className="text-base text-slate-100">{trace.search_query ?? "n/a"}</p>
            </section>

            <section className="space-y-3">
              <h3 className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">
                Top Candidates
              </h3>
              <div className="space-y-3">
                {trace.candidates.map((candidate) => (
                  <article
                    className="rounded-[20px] border border-white/5 bg-white/[0.02] p-4"
                    key={candidate.video_id}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm text-slate-500">#{candidate.rank}</p>
                        <h4 className="text-lg font-semibold text-white">{candidate.video_title}</h4>
                        <p className="text-sm text-slate-300">
                          {candidate.channel ?? "Unknown channel"} | {candidate.video_id}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-500">Confidence</p>
                        <p className="text-lg font-semibold text-slate-100">
                          {candidate.confidence.toFixed(2)}
                        </p>
                      </div>
                    </div>
                    <p className="mt-3 text-sm text-slate-400">
                      Duration: {candidate.duration_seconds ?? "n/a"}s
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {candidate.contributions.map((contribution) => (
                        <span
                          className="rounded-full border border-white/8 bg-black/20 px-3 py-1 text-xs text-slate-300"
                          key={`${candidate.video_id}-${contribution.label}-${contribution.value}`}
                          title={contribution.detail}
                        >
                          {contribution.label}: {contribution.value >= 0 ? "+" : ""}
                          {contribution.value.toFixed(2)}
                        </span>
                      ))}
                    </div>
                    <p className="mt-3 text-sm text-slate-400">
                      Reason: {candidate.reasons.join(", ") || "n/a"}
                    </p>
                    {candidate.lost_reason ? (
                      <p className="mt-2 text-sm text-amber-200">Why it lost: {candidate.lost_reason}</p>
                    ) : null}
                  </article>
                ))}
              </div>
            </section>

            <section className="grid gap-3 md:grid-cols-2">
              <DebugItem label="Winning Candidate" value={trace.winner.video_title ?? "No reliable match"} />
              <DebugItem label="Winning Video ID" value={trace.winner.video_id ?? "n/a"} />
              <DebugItem label="Confidence" value={trace.confidence.toFixed(2)} />
              <DebugItem label="Cache Hit" value={trace.cache_hit ? "yes" : "no"} />
            </section>

            <section className="rounded-[20px] border border-white/5 bg-white/[0.02] p-4">
              <h3 className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Reason</h3>
              <p className="mt-2 text-sm text-slate-200">{trace.reason}</p>
            </section>
          </>
        ) : (
          <p className="text-sm text-slate-400">No resolver trace available for this room yet.</p>
        )}
      </div>
    </details>
  );
}
