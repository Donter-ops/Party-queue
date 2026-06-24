import type { CreateSongPayload, RoomDetail } from "../App";
import { SongForm } from "./SongForm";
import { SongList } from "./SongList";

interface RoomViewProps {
  isRefreshing: boolean;
  room: RoomDetail;
  onAddSong: (payload: CreateSongPayload) => Promise<void>;
}

export function RoomView({
  isRefreshing,
  room,
  onAddSong,
}: RoomViewProps): JSX.Element {
  return (
    <section className="grid w-full max-w-6xl gap-6 lg:grid-cols-[1.2fr_0.8fr]">
      <div className="rounded-[2rem] bg-white p-8 shadow-party sm:p-10">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.28em] text-vinyl/45">
              Room Name
            </p>
            <h1 className="mt-3 text-4xl font-extrabold tracking-tight text-vinyl">
              🎵 {room.name}
            </h1>
          </div>

          <div className="rounded-full bg-mint/35 px-4 py-2 text-sm font-semibold text-vinyl">
            {isRefreshing ? "Refreshing..." : `${room.songs.length} songs queued`}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-bold text-vinyl">Song Queue</h2>
            <p className="mt-2 text-sm text-vinyl/65">
              Die Liste wird nach Position sortiert und nach jedem neuen Song direkt aktualisiert.
            </p>
          </div>

          <SongList songs={room.songs} />
        </div>
      </div>

      <div className="rounded-[2rem] bg-vinyl p-8 text-white shadow-party sm:p-10">
        <h2 className="text-2xl font-bold">Add Song</h2>
        <p className="mt-2 text-sm text-white/70">
          Füge den nächsten Track hinzu. Er landet automatisch an der nächsten freien Position.
        </p>

        <div className="mt-8">
          <SongForm onSubmit={onAddSong} />
        </div>
      </div>
    </section>
  );
}
