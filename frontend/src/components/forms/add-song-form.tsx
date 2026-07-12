import { useEffect, useMemo, useState, type FormEvent, type JSX } from "react";
import { Plus } from "lucide-react";

import { searchSongs, type SearchResultItem } from "../../services/search";
import type { CreateSongPayload } from "../../types";
import { Button } from "../ui/button";
import { Input } from "../ui/input";

interface AddSongFormProps {
  initialGuestName?: string;
  onSubmit: (payload: CreateSongPayload) => Promise<void>;
}

interface SongFormState {
  query: string;
  title: string;
  artist: string;
  added_by: string;
}

const initialFormState: SongFormState = {
  query: "",
  title: "",
  artist: "",
  added_by: "",
};

export function AddSongForm({
  initialGuestName = "",
  onSubmit,
}: AddSongFormProps): JSX.Element {
  const [formState, setFormState] = useState<SongFormState>({
    ...initialFormState,
    added_by: initialGuestName,
  });
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
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

  const normalizedFormState = useMemo(
    () => ({
      query: formState.query.trim(),
      title: formState.title.trim(),
      artist: formState.artist.trim(),
      added_by: formState.added_by.trim(),
    }),
    [formState],
  );

  useEffect(() => {
    const searchQuery = normalizedFormState.query;
    if (searchQuery.length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void (async () => {
        try {
          setValidationMessage(null);
          setIsSearching(true);
          const results = await searchSongs(searchQuery);
          setSearchResults(results);
        } catch {
          setSearchResults([]);
          setValidationMessage("Search could not be completed.");
        } finally {
          setIsSearching(false);
        }
      })();
    }, 300);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [normalizedFormState.query]);

  function handleChange(field: keyof SongFormState, value: string): void {
    setValidationMessage(null);
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }));
  }

  async function submitSong(): Promise<void> {
    if (
      !normalizedFormState.title ||
      !normalizedFormState.artist ||
      !normalizedFormState.added_by
    ) {
      setValidationMessage("Please complete title, artist, and added by.");
      return;
    }

    try {
      setIsSubmitting(true);
      await onSubmit({
        title: normalizedFormState.title,
        artist: normalizedFormState.artist,
        added_by: normalizedFormState.added_by,
        source: "manual",
        external_url: null,
      });

      setFormState({
        ...initialFormState,
        added_by: normalizedFormState.added_by,
      });
      setSearchResults([]);
      setValidationMessage(null);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitSelectedResult(result: SearchResultItem): Promise<void> {
    const addedBy = normalizedFormState.added_by;
    if (!addedBy) {
      setValidationMessage("Please enter who is adding the song first.");
      setFormState((currentState) => ({
        ...currentState,
        title: result.title,
        artist: result.artist,
      }));
      return;
    }

    try {
      setIsSubmitting(true);
      setValidationMessage(null);
      await onSubmit({
        title: result.title,
        artist: result.artist,
        added_by: addedBy,
        source: result.provider,
        external_url: result.external_url ?? null,
      });
      setFormState({
        ...initialFormState,
        added_by: addedBy,
      });
      setSearchResults([]);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await submitSong();
  }

  return (
    <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300" htmlFor="song-search">
          Search
        </label>
        <Input
          id="song-search"
          onChange={(event) => {
            handleChange("query", event.target.value);
          }}
          placeholder="Search for a song..."
          value={formState.query}
        />
      </div>

      {formState.query.trim().length > 1 ? (
        <div className="space-y-2">
          {isSearching ? (
            <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">
              Searching...
            </div>
          ) : null}

          {!isSearching && searchResults.length === 0 ? (
            <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">
              No matches found.
            </div>
          ) : null}

          {searchResults.map((song) => (
            <button
              key={`${song.provider}-${song.artist}-${song.title}`}
              className="flex w-full items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-left transition hover:border-white/16 hover:bg-white/[0.05]"
              disabled={isSubmitting}
              onClick={() => {
                void submitSelectedResult(song);
              }}
              type="button"
            >
              <div>
                <p className="font-medium text-white">{song.title}</p>
                <p className="text-sm text-slate-400">
                  {song.artist} · {song.provider} · {Math.round(song.confidence * 100)}%
                </p>
              </div>
              <Plus className="h-5 w-5 text-slate-400" />
            </button>
          ))}
        </div>
      ) : null}

      <div className="grid gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300" htmlFor="song-title">
            Title
          </label>
          <Input
            id="song-title"
            onChange={(event) => {
              handleChange("title", event.target.value);
            }}
            placeholder="Nights"
            value={formState.title}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300" htmlFor="song-artist">
            Artist
          </label>
          <Input
            id="song-artist"
            onChange={(event) => {
              handleChange("artist", event.target.value);
            }}
            placeholder="Frank Ocean"
            value={formState.artist}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300" htmlFor="song-added-by">
            Added by
          </label>
          <Input
            id="song-added-by"
            onChange={(event) => {
              handleChange("added_by", event.target.value);
            }}
            placeholder="Mara"
            value={formState.added_by}
          />
        </div>
      </div>

      {validationMessage ? (
        <p className="rounded-2xl border border-amber-300/12 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
          {validationMessage}
        </p>
      ) : null}

      <Button className="w-full gap-2" disabled={isSubmitting} size="lg" type="submit">
        <Plus className="h-4 w-4" />
        {isSubmitting ? "Adding song..." : "Add to queue"}
      </Button>
    </form>
  );
}
