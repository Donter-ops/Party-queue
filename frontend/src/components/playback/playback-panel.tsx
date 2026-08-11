import { useEffect, useRef, useMemo, type JSX } from "react";

import type { PlaybackSession, ResolverDebugTrace, Song } from "../../types";
import { Card, CardContent } from "../ui/card";
import { NowPlaying } from "./now-playing";
import { PlaybackControls } from "./playback-controls";
import { Player } from "./player";
import type { YouTubePlayerHandle } from "../player/youtube-player";

interface PlaybackPanelProps {
  onPlaybackFinished: () => Promise<void>;
  onPlaybackNext: () => Promise<void>;
  onPlaybackPrevious: () => Promise<void>;
  onPlaybackToggle: () => Promise<void>;
  playbackSession: PlaybackSession | null;
  resolverDebugTrace: ResolverDebugTrace | null;
  sortedSongs: Song[];
}

export function PlaybackPanel({
  onPlaybackFinished,
  onPlaybackNext,
  onPlaybackPrevious,
  onPlaybackToggle,
  playbackSession,
  resolverDebugTrace,
  sortedSongs,
}: PlaybackPanelProps): JSX.Element {
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
  const isPlaybackButtonDisabled =
    sortedSongs.length === 0 && playbackSession?.current_song == null;

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

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <NowPlaying
          artist={currentSong?.artist ?? null}
          provider={currentProvider ?? currentSong?.source ?? null}
          title={currentSong?.title ?? null}
        />
        <PlaybackControls
          canGoPrevious={Boolean(playbackSession?.previous_available)}
          disabled={isPlaybackButtonDisabled}
          onNext={onPlaybackNext}
          onPrevious={onPlaybackPrevious}
          onToggle={onPlaybackToggle}
          state={playbackSession?.state ?? null}
        />
      </div>

      <Card className="border-white/5">
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
              Player
            </p>
            <h2 className="text-2xl font-semibold tracking-[-0.04em] text-white">
              Shared Playback
            </h2>
          </div>

          <Player
            onPlaybackFinished={onPlaybackFinished}
            playerRef={playerRef}
            shouldRenderYouTubePlayer={shouldRenderYouTubePlayer}
            videoId={playbackSession?.youtube_video_id ?? null}
          />

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
  const hasSpotifyArtists = useMemo(
    () => Boolean(trace?.spotify?.artists.length),
    [trace?.spotify?.artists],
  );

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
                <DebugItem
                  label="Artists"
                  value={hasSpotifyArtists ? trace.spotify?.artists.join(", ") ?? "n/a" : "n/a"}
                />
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
