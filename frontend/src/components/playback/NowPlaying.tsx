type NowPlayingProps = {
  title: string;
 artist: string;
  addedBy: string;
};

export default function NowPlaying({
  title,
  artist,
  addedBy,
}: NowPlayingProps) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-8 shadow-lg">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
        Now Playing
      </p>

      <h1 className="mt-4 text-4xl font-bold">
        {title}
      </h1>

      <p className="mt-2 text-lg text-slate-300">
        {artist}
      </p>

      <p className="mt-6 text-sm text-slate-500">
        Added by {addedBy}
      </p>
    </section>
  );
}