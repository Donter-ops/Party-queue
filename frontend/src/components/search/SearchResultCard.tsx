type Props = {
  title: string;
  artist: string;
  onAdd: () => void;
};

export default function SearchResultCard({
  title,
  artist,
  onAdd,
}: Props) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900 p-4">

      <div>

        <h3 className="font-medium">
          {title}
        </h3>

        <p className="text-slate-400">
          {artist}
        </p>

      </div>

      <button
        onClick={onAdd}
        className="rounded-lg bg-white px-4 py-2 text-black"
      >
        Add
      </button>

    </div>
  );
}