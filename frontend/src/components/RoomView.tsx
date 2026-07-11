import { useMemo, useState } from "react";
import type { JSX } from "react";

import type { CreateSongPayload, RoomDetail } from "../App";
import { SongForm } from "./SongForm";
import { SongList } from "./SongList";

interface RoomViewProps {
  autoRefreshEnabled: boolean;
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
  onToggleAutoRefresh: () => void;
}

export function RoomView({
  autoRefreshEnabled,
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
  onToggleAutoRefresh,
}: RoomViewProps): JSX.Element {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedGuest, setSelectedGuest] = useState("all");

  const sortedSongs = useMemo(
    () => [...room.songs].sort((leftSong, rightSong) => leftSong.position - rightSong.position),
    [room.songs],
  );

  const guestOptions = useMemo(
    () => Array.from(new Set(sortedSongs.map((song) => song.added_by))).sort(),
    [sortedSongs],
  );

  const sourceCounts = useMemo(
    () =>
      sortedSongs.reduce<Record<string, number>>((accumulator, song) => {
        accumulator[song.source] = (accumulator[song.source] ?? 0) + 1;
        return accumulator;
      }, {}),
    [sortedSongs],
  );

  const filteredSongs = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return sortedSongs.filter((song) => {
      const matchesGuest = selectedGuest === "all" || song.added_by === selectedGuest;
      const matchesSearch =
        !normalizedSearch ||
        song.title.toLowerCase().includes(normalizedSearch) ||
        song.artist.toLowerCase().includes(normalizedSearch) ||
        song.added_by.toLowerCase().includes(normalizedSearch);

      return matchesGuest && matchesSearch;
    });
  }, [searchTerm, selectedGuest, sortedSongs]);

  const topGuest = useMemo(() => {
    const counts = sortedSongs.reduce<Record<string, number>>((accumulator, song) => {
      accumulator[song.added_by] = (accumulator[song.added_by] ?? 0) + 1;
      return accumulator;
    }, {});

    return Object.entries(counts).sort((leftEntry, rightEntry) => rightEntry[1] - leftEntry[1])[0];
  }, [sortedSongs]);

  const nextUpSong = sortedSongs[0] ?? null;
  const queueDuration = sortedSongs.length * 4;

  return (
    <section className="grid w-full gap-6 xl:grid-cols-[1.35fr_0.65fr]">
      <div className="space-y-6">
        <div className="overflow-hidden rounded-[2.25rem] bg-vinyl text-white shadow-party">
          <div className="relative px-8 py-8 sm:px-10 sm:py-10">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.14),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(141,211,199,0.18),transparent_28%)]" />

            <div className="relative space-y-8">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-4">
                  <p className="inline-flex rounded-full border border-white/15 bg-white/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.28em] text-white/72">
                    Live Room
                  </p>
                  <div>
                    <h1 className="text-4xl font-black tracking-[-0.04em] sm:text-5xl">
                      {room.name}
                    </h1>
                    <p className="mt-3 text-sm text-white/68">
                      Room-ID: <span className="font-semibold text-white">{room.id}</span>
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    className="rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white hover:text-vinyl"
                    onClick={() => {
                      void onRefreshRoom();
                    }}
                    type="button"
                  >
                    {isRefreshing ? "Aktualisiert..." : "Jetzt aktualisieren"}
                  </button>
                  <button
                    className="rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white hover:text-vinyl"
                    onClick={() => {
                      void onCopyShareLink();
                    }}
                    type="button"
                  >
                    Link kopieren
                  </button>
                  <button
                    className="rounded-full border border-white/15 bg-transparent px-4 py-2 text-sm font-semibold text-white/82 transition hover:border-white hover:text-white"
                    onClick={onLeaveRoom}
                    type="button"
                  >
                    Raum verlassen
                  </button>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-4">
                <StatCard label="Songs in Queue" value={String(sortedSongs.length)} />
                <StatCard label="Nächster Song" value={nextUpSong ? nextUpSong.artist : "Noch leer"} />
                <StatCard label="Geschätzte Dauer" value={`${queueDuration} min`} />
                <StatCard
                  label="Top Gastgeber:in"
                  value={topGuest ? `${topGuest[0]} (${topGuest[1]})` : "Noch offen"}
                />
              </div>

              <div className="grid gap-4 lg:grid-cols-[1fr_auto_auto]">
                <label className="block">
                  <span className="sr-only">Songs durchsuchen</span>
                  <input
                    className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none transition placeholder:text-white/45 focus:border-gold focus:bg-white/15"
                    onChange={(event) => {
                      setSearchTerm(event.target.value);
                    }}
                    placeholder="Nach Titel, Artist oder Gast suchen"
                    type="text"
                    value={searchTerm}
                  />
                </label>

                <select
                  className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm font-semibold text-white outline-none transition focus:border-gold focus:bg-white/15"
                  onChange={(event) => {
                    setSelectedGuest(event.target.value);
                  }}
                  value={selectedGuest}
                >
                  <option className="text-vinyl" value="all">
                    Alle Gäste
                  </option>
                  {guestOptions.map((guest) => (
                    <option key={guest} className="text-vinyl" value={guest}>
                      {guest}
                    </option>
                  ))}
                </select>

                <button
                  className={`rounded-2xl px-4 py-3 text-sm font-bold transition ${
                    autoRefreshEnabled
                      ? "bg-gold text-vinyl hover:bg-white"
                      : "border border-white/15 bg-white/10 text-white hover:bg-white hover:text-vinyl"
                  }`}
                  onClick={onToggleAutoRefresh}
                  type="button"
                >
                  {autoRefreshEnabled ? "Auto-Refresh aktiv" : "Auto-Refresh aus"}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-[2rem] bg-white p-6 shadow-party sm:p-8">
          <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="text-2xl font-black tracking-tight text-vinyl">Queue Übersicht</h2>
              <p className="mt-2 text-sm text-vinyl/62">
                Filtere die Liste, priorisiere Songs und entferne Duplikate direkt im
                Dashboard.
              </p>
            </div>

            <div className="rounded-full bg-cream px-4 py-2 text-sm font-semibold text-vinyl">
              {filteredSongs.length} von {sortedSongs.length} Songs sichtbar
            </div>
          </div>

          <SongList
            songs={filteredSongs}
            onDeleteSong={onDeleteSong}
            onMoveSong={onMoveSong}
          />
        </div>
      </div>

      <aside className="space-y-6">
        <div className="rounded-[2rem] bg-white p-6 shadow-party sm:p-8">
          <h2 className="text-2xl font-black tracking-tight text-vinyl">Song hinzufügen</h2>
          <p className="mt-2 text-sm text-vinyl/62">
            Neue Tracks landen automatisch auf dem nächsten freien Slot. Spotify und
            YouTube Music sind jetzt als Quellen vorbereitet.
          </p>

          <div className="mt-6">
            <SongForm initialGuestName={savedGuestName} onSubmit={onAddSong} />
          </div>
        </div>

        <div className="rounded-[2rem] bg-white p-6 shadow-party sm:p-8">
          <h3 className="text-lg font-black tracking-tight text-vinyl">Share & Status</h3>

          <div className="mt-5 space-y-4">
            <div className="rounded-[1.5rem] bg-cream/80 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-vinyl/45">
                Share-Link
              </p>
              <p className="mt-2 break-all text-sm text-vinyl/72">{roomShareUrl}</p>
            </div>

            <div className="rounded-[1.5rem] border border-vinyl/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-vinyl/45">
                Jetzt als nächstes
              </p>
              <p className="mt-2 text-base font-bold text-vinyl">
                {nextUpSong ? `${nextUpSong.artist} - ${nextUpSong.title}` : "Noch kein Track"}
              </p>
              <p className="mt-1 text-sm text-vinyl/55">
                {nextUpSong ? `eingereicht von ${nextUpSong.added_by}` : "Fülle die Queue, um loszulegen."}
              </p>
            </div>

            <div className="rounded-[1.5rem] border border-vinyl/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-vinyl/45">
                Quellen-Mix
              </p>
              <div className="mt-3 grid gap-2 text-sm text-vinyl/70">
                <p>Manuell: {sourceCounts.manual ?? 0}</p>
                <p>Spotify: {sourceCounts.spotify ?? 0}</p>
                <p>YouTube Music: {sourceCounts.youtube_music ?? 0}</p>
              </div>
            </div>

            {errorMessage ? (
              <div className="rounded-[1.5rem] border border-coral/20 bg-coral/8 px-4 py-3 text-sm font-medium text-vinyl">
                {errorMessage}
              </div>
            ) : null}
          </div>
        </div>
      </aside>
    </section>
  );
}

interface StatCardProps {
  label: string;
  value: string;
}

function StatCard({ label, value }: StatCardProps): JSX.Element {
  return (
    <div className="rounded-[1.5rem] border border-white/12 bg-white/8 p-4 backdrop-blur-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/62">{label}</p>
      <p className="mt-3 text-lg font-bold text-white">{value}</p>
    </div>
  );
}
