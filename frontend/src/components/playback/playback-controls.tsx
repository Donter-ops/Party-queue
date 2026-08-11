import { Pause, Play, SkipBack, SkipForward } from "lucide-react";
import type { JSX, ReactNode } from "react";

import { Button } from "../ui/button";

interface PlaybackControlsProps {
  canGoPrevious: boolean;
  disabled: boolean;
  onNext: () => Promise<void>;
  onPrevious: () => Promise<void>;
  onToggle: () => Promise<void>;
  state: "IDLE" | "PLAYING" | "PAUSED" | "FINISHED" | "SKIPPED" | null;
}

export function PlaybackControls({
  canGoPrevious,
  disabled,
  onNext,
  onPrevious,
  onToggle,
  state,
}: PlaybackControlsProps): JSX.Element {
  const playbackButtonLabel =
    state === "PLAYING" ? "Pause" : state === "PAUSED" ? "Resume" : "Play";
  const playbackButtonIcon: ReactNode =
    state === "PLAYING" ? (
      <Pause className="h-4 w-4" />
    ) : (
      <Play className="h-4 w-4 fill-current" />
    );

  return (
    <div className="flex flex-wrap gap-3 rounded-full border border-white/8 bg-black/25 p-1.5 shadow-[0_18px_60px_rgba(15,23,42,0.22)]">
      <Button
        className="gap-2 rounded-full"
        disabled={!canGoPrevious}
        onClick={() => {
          void onPrevious();
        }}
        variant="secondary"
      >
        <SkipBack className="h-4 w-4" />
        Previous
      </Button>
      <Button
        className="gap-2 rounded-full"
        disabled={disabled}
        onClick={() => {
          void onToggle();
        }}
        variant="secondary"
      >
        {playbackButtonIcon}
        {playbackButtonLabel}
      </Button>
      <Button
        className="gap-2 rounded-full"
        disabled={disabled}
        onClick={() => {
          void onNext();
        }}
        variant="secondary"
      >
        <SkipForward className="h-4 w-4" />
        Next
      </Button>
    </div>
  );
}
