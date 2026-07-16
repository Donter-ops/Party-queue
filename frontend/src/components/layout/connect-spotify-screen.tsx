import { Music4 } from "lucide-react";
import { type JSX } from "react";

import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";

const spotifyLoginUrl = `${window.location.protocol}//${window.location.hostname}:8000/auth/spotify/login`;

interface ConnectSpotifyScreenProps {
  status: "idle" | "success" | "error";
  errorMessage: string | null;
}

export function ConnectSpotifyScreen({
  status,
  errorMessage,
}: ConnectSpotifyScreenProps): JSX.Element {
  return (
    <section className="grid min-h-[calc(100vh-12rem)] place-items-center">
      <Card className="w-full max-w-xl">
        <CardContent className="space-y-8">
          <div className="space-y-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-3xl bg-white text-slate-950">
              <Music4 className="h-6 w-6" />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
                Host setup
              </p>
              <h1 className="text-4xl font-semibold tracking-[-0.04em] text-white">
                Connect Spotify
              </h1>
              <p className="text-sm leading-6 text-slate-400">
                Connect the host Spotify account before playback integration is enabled.
              </p>
            </div>
          </div>

          {status === "success" ? (
            <p className="rounded-2xl border border-emerald-400/12 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
              Spotify connected successfully.
            </p>
          ) : null}

          {status === "error" ? (
            <p className="rounded-2xl border border-rose-400/12 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {errorMessage || "Spotify authentication failed."}
            </p>
          ) : null}

          <Button
            className="w-full"
            onClick={() => {
              window.location.href = spotifyLoginUrl;
            }}
            size="lg"
            type="button"
          >
            Connect Spotify
          </Button>
        </CardContent>
      </Card>
    </section>
  );
}
