import { useEffect, useMemo, useRef, useState, type FormEvent, type JSX } from "react";
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
  added_by: string;
}

const initialFormState: SongFormState = {
  query: "",
  added_by: "",
};

const urlPattern = /^(https?:\/\/|spotify:track:)/i;

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
  const lastAutoSubmittedInputRef = useRef<string | null>(null);

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
      added_by: formState.added_by.trim(),
    }),
    [formState],
  );
  const isUrlInput = urlPattern.test(normalizedFormState.query);

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

          const autoSubmitKey = `${searchQuery}:${normalizedFormState.added_by}`;
          if (
            urlPattern.test(searchQuery) &&
            normalizedFormState.added_by &&
            results.length > 0 &&
            lastAutoSubmittedInputRef.current !== autoSubmitKey
          ) {
            lastAutoSubmittedInputRef.current = autoSubmitKey;
            await submitSelectedResult(results[0], normalizedFormState.added_by);
          }
        } catch {
          setSearchResults([]);
          setValidationMessage(
            urlPattern.test(searchQuery)
              ? "Link could not be resolved."
              : "Search could not be completed.",
          );
        } finally {
          setIsSearching(false);
        }
      })();
    }, 300);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [normalizedFormState.added_by, normalizedFormState.query]);

  function handleChange(field: keyof SongFormState, value: string): void {
    setValidationMessage(null);
    if (field === "query") {
      lastAutoSubmittedInputRef.current = null;
    }
    setFormState((currentState) => ({
      ...currentState,
      [field]: value,
    }));
  }

  async function submitSong(): Promise<void> {
    if (!normalizedFormState.added_by) {
      setValidationMessage("Please enter who is adding the song.");
      return;
    }

    if (!normalizedFormState.query) {
      setValidationMessage("Please enter a song title or paste a link.");
      return;
    }

    if (searchResults.length === 0) {
      setValidationMessage(
        isUrlInput
          ? "This link could not be resolved yet."
          : "Select a search result to add it to the queue.",
      );
      return;
    }

    await submitSelectedResult(searchResults[0], normalizedFormState.added_by);
  }

  async function submitSelectedResult(
    result: SearchResultItem,
    addedByOverride?: string,
  ): Promise<void> {
    const addedBy = addedByOverride ?? normalizedFormState.added_by;
    if (!addedBy) {
      setValidationMessage("Please enter who is adding the song first.");
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
      lastAutoSubmittedInputRef.current = null;
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
          Song or link
        </label>
        <Input
          id="song-search"
          onChange={(event) => {
            handleChange("query", event.target.value);
          }}
          placeholder="Search for a song or paste a YouTube / Spotify link..."
          value={formState.query}
        />
      </div>

      {formState.query.trim().length > 1 ? (
        <div className="space-y-2">
          {isSearching ? (
            <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">
              {isUrlInput ? "Resolving link..." : "Searching..."}
            </div>
          ) : null}

          {!isSearching && searchResults.length === 0 ? (
            <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">
              {isUrlInput ? "No playable song found for this link." : "No matches found."}
            </div>
          ) : null}

          {searchResults.map((song) => (
            <button
              key={`${song.provider}-${song.external_id}`}
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
        {isSubmitting ? "Adding song..." : isUrlInput ? "Add link to queue" : "Add to queue"}
      </Button>
    </form>
  );
}
