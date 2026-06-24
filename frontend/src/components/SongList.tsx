import type { Song } from "../App";

interface SongListProps {
  songs: Song[];
}

export function SongList({ songs }: SongListProps): JSX.Element {
  const sortedSongs = [...songs].sort((leftSong, rightSong) => leftSong.position - rightSong.position);

  if (sortedSongs.length === 0) {
    return (
      <div className="rounded-[1.5rem] border border-dashed border-vinyl/15 bg-cream/70 px-6 py-10 text-center text-vinyl/55">
        Noch keine Songs in der Queue.
      </div>
    );
  }

  return (
    <ol className="space-y-3">
      {sortedSongs.map((song) => (
        <li
          key={song.id}
          className="flex items-start gap-4 rounded-[1.5rem] border border-vinyl/8 bg-cream/65 px-5 py-4"
        >
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-vinyl text-sm font-bold text-white">
            {song.position + 1}
          </div>

          <div className="min-w-0">
            <p className="truncate text-lg font-semibold text-vinyl">{song.artist}</p>
            <p className="truncate text-sm text-vinyl/65">{song.title}</p>
            <p className="mt-1 text-sm text-vinyl/55">added by {song.added_by}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
