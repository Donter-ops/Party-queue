import { useState } from "react";

import type { CreateSongPayload } from "../App";

interface SongFormProps {
  onSubmit: (payload: CreateSongPayload) => Promise<void>;
}

interface SongFormState {
  title: string;
  artist: string;
  added_by: string;
}

const initialFormState: SongFormState = {
  title: "",
  artist: "",
  added_by: "",
};

export function SongForm({ onSubmit }: SongFormProps): JSX.Element {
  const [formState, setFormState] = useState<SongFormState>(initialFormState);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(field: keyof SongFormState, value: string): void {
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (!formState.title || !formState.artist || !formState.added_by) {
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit({
        ...formState,
        source: "manual",
      });
      setFormState(initialFormState);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-white/80">Titel</span>
        <input
          className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none transition placeholder:text-white/35 focus:border-gold focus:bg-white/15"
          onChange={(event) => {
            handleChange("title", event.target.value);
          }}
          placeholder="Bohemian Rhapsody"
          type="text"
          value={formState.title}
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-white/80">Künstler</span>
        <input
          className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none transition placeholder:text-white/35 focus:border-gold focus:bg-white/15"
          onChange={(event) => {
            handleChange("artist", event.target.value);
          }}
          placeholder="Queen"
          type="text"
          value={formState.artist}
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-white/80">Dein Name</span>
        <input
          className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none transition placeholder:text-white/35 focus:border-gold focus:bg-white/15"
          onChange={(event) => {
            handleChange("added_by", event.target.value);
          }}
          placeholder="Tim"
          type="text"
          value={formState.added_by}
        />
      </label>

      <button
        className="w-full rounded-full bg-gold px-5 py-4 text-base font-bold text-vinyl transition hover:-translate-y-0.5 hover:bg-coral hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Adding Song..." : "Add Song"}
      </button>
    </form>
  );
}
