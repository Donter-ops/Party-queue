type PlaybackControlsProps = {
  onFinish: () => void;
};

export default function PlaybackControls({
  onFinish,
}: PlaybackControlsProps) {
  return (
    <section className="mt-8 flex justify-end">

      <button
        onClick={onFinish}
        className="rounded-xl bg-white px-6 py-3 font-semibold text-black transition hover:opacity-90"
      >
        Finish Current Song
      </button>

    </section>
  );
}