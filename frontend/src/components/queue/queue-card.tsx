import type { JSX } from "react";
import { ArrowDown, ArrowUp, Link2, Trash2 } from "lucide-react";

import type { Song } from "../../types";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";

interface QueueCardProps {
  canMoveDown: boolean;
  canMoveUp: boolean;
  isBusy: boolean;
  onDelete: () => void;
  onMoveDown: () => void;
  onMoveUp: () => void;
  song: Song;
}

export function QueueCard({
  canMoveDown,
  canMoveUp,
  isBusy,
  onDelete,
  onMoveDown,
  onMoveUp,
  song,
}: QueueCardProps): JSX.Element {
  return (
    <Card className="overflow-hidden">
      <CardContent className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] bg-white text-lg font-semibold text-slate-950">
            {song.position + 1}
          </div>

          <div className="min-w-0 space-y-1">
            <div className="flex flex-wrap items-center gap-3">
              <h3 className="truncate text-2xl font-semibold tracking-[-0.03em] text-white">
                {song.title}
              </h3>
              <span className="rounded-full border border-white/8 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                {song.source.split("_").join(" ")}
              </span>
            </div>
            <p className="text-base text-slate-300">{song.artist}</p>
            <p className="text-sm text-slate-500">Added by {song.added_by}</p>
            {song.external_url ? (
              <a
                className="inline-flex items-center gap-2 text-sm font-medium text-slate-300 transition hover:text-white"
                href={song.external_url}
                rel="noreferrer"
                target="_blank"
              >
                <Link2 className="h-4 w-4" />
                Open source
              </a>
            ) : null}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button disabled={isBusy || !canMoveUp} onClick={onMoveUp} size="icon" variant="outline">
            <ArrowUp className="h-4 w-4" />
          </Button>
          <Button
            disabled={isBusy || !canMoveDown}
            onClick={onMoveDown}
            size="icon"
            variant="outline"
          >
            <ArrowDown className="h-4 w-4" />
          </Button>
          <Button disabled={isBusy} onClick={onDelete} size="icon" variant="danger">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
