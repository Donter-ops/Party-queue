import type { JSX, RefObject } from "react";

import { YouTubePlayer, type YouTubePlayerHandle } from "../player/youtube-player";

interface PlayerProps {
  onPlaybackFinished: () => Promise<void>;
  playerRef: RefObject<YouTubePlayerHandle | null>;
  shouldRenderYouTubePlayer: boolean;
  videoId: string | null;
}

export function Player({
  onPlaybackFinished,
  playerRef,
  shouldRenderYouTubePlayer,
  videoId,
}: PlayerProps): JSX.Element {
  if (!shouldRenderYouTubePlayer) {
    return (
      <div className="flex aspect-video min-h-[240px] items-center justify-center rounded-[28px] bg-black/30 px-6 text-center text-sm text-slate-400 shadow-[0_24px_80px_rgba(15,23,42,0.2)]">
        Add a YouTube or YouTube Music link to play the video directly in the room.
      </div>
    );
  }

  return (
    <YouTubePlayer
      ref={playerRef}
      onEnded={() => {
        void onPlaybackFinished();
      }}
      videoId={videoId}
    />
  );
}
