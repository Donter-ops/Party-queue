interface CreateRoomProps {
  errorMessage: string | null;
  isLoading: boolean;
  onCreateRoom: () => Promise<void>;
}

export function CreateRoom({
  errorMessage,
  isLoading,
  onCreateRoom,
}: CreateRoomProps): JSX.Element {
  return (
    <section className="w-full max-w-2xl overflow-hidden rounded-[2rem] bg-white shadow-party">
      <div className="relative isolate px-8 py-12 sm:px-12 sm:py-16">
        <div className="absolute -left-16 top-0 h-40 w-40 rounded-full bg-gold/25 blur-3xl" />
        <div className="absolute right-0 top-10 h-48 w-48 rounded-full bg-mint/30 blur-3xl" />

        <div className="relative space-y-8">
          <div className="space-y-4">
            <p className="inline-flex rounded-full bg-vinyl px-4 py-2 text-xs font-bold uppercase tracking-[0.28em] text-white">
              House Party Control
            </p>
            <h1 className="text-4xl font-extrabold tracking-tight text-vinyl sm:text-6xl">
              🎵 PartyQueue
            </h1>
            <p className="max-w-xl text-base text-vinyl/70 sm:text-lg">
              Erstelle in einem Klick einen neuen Raum und sammle Songs direkt in einer klaren Queue.
            </p>
          </div>

          <button
            className="inline-flex items-center justify-center rounded-full bg-coral px-8 py-4 text-base font-semibold text-white transition hover:-translate-y-0.5 hover:bg-vinyl disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            onClick={() => {
              void onCreateRoom();
            }}
            type="button"
          >
            {isLoading ? "Creating Room..." : "Create Room"}
          </button>

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
