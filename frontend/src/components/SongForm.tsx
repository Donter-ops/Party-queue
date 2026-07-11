import { useEffect, useMemo, useState } from "react";
import type { FormEvent, JSX } from "react";

import type { CreateSongPayload } from "../App";

type SongSource = "manual" | "spotify" | "youtube_music";

interface SongFormProps {
  initialGuestName?: string;
  onSubmit: (payload: CreateSongPayload) => Promise<void>;
}

interface SongFormState {
  title: string;
  artist: string;
  added_by: string;
  external_url: string;
}

const initialFormState: SongFormState = {
  title: "",
  artist: "",
  added_by: "",
  external_url: "",
};

const sourceOptions: Array<{
  description: string;
  id: SongSource;
  label: string;
}> = [
  {
    id: "manual",
    label: "Manuell",
    description: "Schneller Eintrag nur mit Titel und Künstler:in.",
  },
  {
    id: "spotify",
    label: "Spotify",
    description: "Track-Link speichern und Quelle in der Queue sichtbar machen.",
  },
  {
    id: "youtube_music",
    label: "YouTube Music",
    description: "YouTube-Music-Link einfügen und später direkt öffnen.",
  },
];

export function SongForm({
  initialGuestName = "",
  onSubmit,
}: SongFormProps): JSX.Element {
  const [source, setSource] = useState<SongSource>("manual");
  const [formState, setFormState] = useState<SongFormState>({
    ...initialFormState,
    added_by: initialGuestName,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  useEffect(() => {
    setFormState((currentState) =>
      currentState.added_by
        ? currentState
        : {
            ...currentState,
            added_by: initialGuestName,
          },
    );
  }, [initialGuestName]);

  function handleChange(field: keyof SongFormState, value: string): void {
    setValidationMessage(null);
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }));
  }

  const normalizedFormState = useMemo(
    () => ({
      title: formState.title.trim(),
      artist: formState.artist.trim(),
      added_by: formState.added_by.trim(),
      external_url: formState.external_url.trim(),
    }),
    [formState],
  );

  const requiresLink = source !== "manual";
  const canSubmit =
    normalizedFormState.title.length > 0 &&
    normalizedFormState.artist.length > 0 &&
    normalizedFormState.added_by.length > 0 &&
    (!requiresLink || normalizedFormState.external_url.length > 0);

  const currentSourceCopy = sourceOptions.find((option) => option.id === source);

  async function submitSong(): Promise<void> {
    if (!canSubmit) {
      setValidationMessage(
        requiresLink
          ? "Bitte fülle Titel, Künstler:in, deinen Namen und den Musik-Link aus."
          : "Bitte fülle Titel, Künstler:in und deinen Namen aus.",
      );
      return;
    }

    try {
      setIsSubmitting(true);
      setValidationMessage(null);
      await onSubmit({
        title: normalizedFormState.title,
        artist: normalizedFormState.artist,
        added_by: normalizedFormState.added_by,
        source,
        external_url: normalizedFormState.external_url || null,
      });
      setFormState({
        ...initialFormState,
        added_by: normalizedFormState.added_by,
      });
      setSource("manual");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await submitSong();
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {sourceOptions.map((option) => (
            <button
              key={option.id}
              className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                source === option.id
                  ? "bg-vinyl text-white"
                  : "border border-vinyl/10 bg-cream/60 text-vinyl hover:border-vinyl hover:bg-white"
              }`}
              onClick={() => {
                setSource(option.id);
                setValidationMessage(null);
              }}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>

        <p className="text-sm text-vinyl/62">{currentSourceCopy?.description}</p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-vinyl/72">Titel</span>
        <input
          className="w-full rounded-2xl border border-vinyl/10 bg-cream/55 px-4 py-3 text-vinyl outline-none transition placeholder:text-vinyl/35 focus:border-coral focus:bg-white"
          onChange={(event) => {
            handleChange("title", event.target.value);
          }}
          placeholder="Bohemian Rhapsody"
          required
          type="text"
          value={formState.title}
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-vinyl/72">Künstler:in</span>
        <input
          className="w-full rounded-2xl border border-vinyl/10 bg-cream/55 px-4 py-3 text-vinyl outline-none transition placeholder:text-vinyl/35 focus:border-coral focus:bg-white"
          onChange={(event) => {
            handleChange("artist", event.target.value);
          }}
          placeholder="Queen"
          required
          type="text"
          value={formState.artist}
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-vinyl/72">Dein Name</span>
        <input
          className="w-full rounded-2xl border border-vinyl/10 bg-cream/55 px-4 py-3 text-vinyl outline-none transition placeholder:text-vinyl/35 focus:border-coral focus:bg-white"
          onChange={(event) => {
            handleChange("added_by", event.target.value);
          }}
          placeholder="Max Mustermann"
          required
          type="text"
          value={formState.added_by}
        />
      </label>

      {requiresLink ? (
        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-vinyl/72">
            {source === "spotify" ? "Spotify-Link" : "YouTube-Music-Link"}
          </span>
          <input
            className="w-full rounded-2xl border border-vinyl/10 bg-cream/55 px-4 py-3 text-vinyl outline-none transition placeholder:text-vinyl/35 focus:border-coral focus:bg-white"
            onChange={(event) => {
              handleChange("external_url", event.target.value);
            }}
            placeholder={
              source === "spotify"
                ? "https://open.spotify.com/track/..."
                : "https://music.youtube.com/watch?v=..."
            }
            required
            type="url"
            value={formState.external_url}
          />
        </label>
      ) : null}

      {validationMessage ? (
        <p className="rounded-2xl border border-coral/20 bg-coral/10 px-4 py-3 text-sm font-medium text-vinyl">
          {validationMessage}
        </p>
      ) : null}

      <button
        className="w-full rounded-full bg-vinyl px-5 py-4 text-base font-bold text-white transition hover:-translate-y-0.5 hover:bg-coral disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isSubmitting}
        onClick={() => {
          void submitSong();
        }}
        type="button"
      >
        {isSubmitting ? "Song wird hinzugefügt..." : "Song zur Queue hinzufügen"}
      </button>
    </form>
  );
}
