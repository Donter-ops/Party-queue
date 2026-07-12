type QueueSong = {
  id: number;
  title: string;
  artist: string;
};

type QueueTimelineProps = {
  songs: QueueSong[];
};

export default function QueueTimeline({
  songs,
}: QueueTimelineProps) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-8 mt-8">

      <h2 className="text-xl font-semibold mb-6">
        Up Next
      </h2>

      <div className="space-y-5">

        {songs.map((song, index) => (

          <div
            key={song.id}
            className="flex items-center gap-5"
          >

            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-700 text-slate-400">

              {index + 1}

            </div>

            <div>

              <h3 className="font-medium">
                {song.title}
              </h3>

              <p className="text-sm text-slate-500">
                {song.artist}
              </p>

            </div>

          </div>

        ))}

      </div>

    </section>
  );
}