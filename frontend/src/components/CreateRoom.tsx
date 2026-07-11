import { useState } from "react";
import type { JSX } from "react";

interface CreateRoomProps {
  errorMessage: string | null;
  isLoading: boolean;
  onCreateRoom: (roomName: string) => Promise<void>;
  onJoinRoom: (roomId: string) => Promise<void>;
}

export function CreateRoom({
  errorMessage,
  isLoading,
  onCreateRoom,
  onJoinRoom,
}: CreateRoomProps): JSX.Element {
  const [roomName, setRoomName] = useState("My Party");
  const [roomId, setRoomId] = useState("");

  return (
    <section className="grid w-full max-w-6xl gap-6 lg:grid-cols-[1.15fr_0.85fr]">
      <div className="relative overflow-hidden rounded-[2.25rem] bg-vinyl px-8 py-10 text-white shadow-party sm:px-10 sm:py-12">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.18),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(242,193,78,0.22),transparent_32%)]" />

        <div className="relative flex h-full flex-col justify-between gap-10">
          <div className="space-y-6">
            <p className="inline-flex rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.28em] text-white/80">
              House Party Control
            </p>
            <div className="space-y-4">
              <h1 className="max-w-2xl text-4xl font-black tracking-[-0.04em] sm:text-6xl">
                PartyQueue für den ganzen Raum.
              </h1>
              <p className="max-w-xl text-base text-white/72 sm:text-lg">
                Erstelle in Sekunden einen Musikraum, teile den Link direkt mit deinen
                Gästen und halte die Queue live im Blick.
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <FeatureCard label="Live Queue" value="Auto-Refresh alle 15s" />
            <FeatureCard label="Raum teilen" value="Link + Room-ID sofort bereit" />
            <FeatureCard label="Moderation" value="Songs verschieben oder löschen" />
          </div>
        </div>
      </div>

      <div className="rounded-[2.25rem] bg-white p-8 shadow-party sm:p-10">
        <div className="space-y-8">
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-vinyl/45">
              Start
            </p>
            <h2 className="text-3xl font-black tracking-tight text-vinyl">
              Neues Layout, schnellere Flows
            </h2>
            <p className="text-sm leading-6 text-vinyl/68">
              Lege einen neuen Raum mit Namen an oder öffne einen bestehenden Raum über
              seine ID.
            </p>
          </div>

          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              void onCreateRoom(roomName.trim() || "My Party");
            }}
          >
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-vinyl/72">Raumname</span>
              <input
                className="w-full rounded-2xl border border-vinyl/10 bg-cream/55 px-4 py-3 text-vinyl outline-none transition focus:border-coral focus:bg-white"
                onChange={(event) => {
                  setRoomName(event.target.value);
                }}
                placeholder="Sommersause auf der Dachterrasse"
                type="text"
                value={roomName}
              />
            </label>

            <button
              className="w-full rounded-full bg-coral px-5 py-4 text-base font-bold text-white transition hover:-translate-y-0.5 hover:bg-vinyl disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isLoading}
              type="submit"
            >
              {isLoading ? "Raum wird erstellt..." : "Neuen Raum erstellen"}
            </button>
          </form>

          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-vinyl/10" />
            <span className="text-xs font-semibold uppercase tracking-[0.24em] text-vinyl/40">
              oder
            </span>
            <div className="h-px flex-1 bg-vinyl/10" />
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-vinyl/72">Room-ID</span>
              <input
                className="w-full rounded-2xl border border-vinyl/10 bg-cream/55 px-4 py-3 text-vinyl outline-none transition focus:border-mint focus:bg-white"
                onChange={(event) => {
                  setRoomId(event.target.value);
                }}
                placeholder="Bestehende Room-ID eingeben"
                type="text"
                value={roomId}
              />
            </label>

            <button
              className="w-full rounded-full border border-vinyl/12 bg-white px-5 py-4 text-base font-bold text-vinyl transition hover:-translate-y-0.5 hover:border-vinyl hover:bg-vinyl hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isLoading || !roomId.trim()}
              onClick={() => {
                void onJoinRoom(roomId.trim());
              }}
              type="button"
            >
              Bestehenden Raum öffnen
            </button>
          </div>

          {errorMessage ? (
            <p className="rounded-2xl border border-coral/20 bg-coral/10 px-4 py-3 text-sm font-medium text-vinyl">
              {errorMessage}
            </p>
          ) : null}
        </div>
      </div>
    </section>
  );
}

interface FeatureCardProps {
  label: string;
  value: string;
}

function FeatureCard({ label, value }: FeatureCardProps): JSX.Element {
  return (
    <div className="rounded-[1.6rem] border border-white/12 bg-white/8 p-4 backdrop-blur-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/60">{label}</p>
      <p className="mt-3 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}
