import { ArrowRight, Link2, PlusCircle } from "lucide-react";
import { useState, type JSX } from "react";

import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { Input } from "../ui/input";

interface CreateRoomScreenProps {
  errorMessage: string | null;
  isLoading: boolean;
  onCreateRoom: (roomName: string) => Promise<void>;
  onJoinRoom: (roomId: string) => Promise<void>;
}

export function CreateRoomScreen({
  errorMessage,
  isLoading,
  onCreateRoom,
  onJoinRoom,
}: CreateRoomScreenProps): JSX.Element {
  const [roomName, setRoomName] = useState("My Party");
  const [roomId, setRoomId] = useState("");

  return (
    <section className="grid min-h-[calc(100vh-12rem)] items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-8">
        <div className="space-y-4">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
            Queue first
          </p>
          <h1 className="max-w-3xl text-5xl font-semibold tracking-[-0.05em] text-white sm:text-6xl">
            A calmer interface for collaborative music rooms.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-slate-400">
            Create a room, share the link, and keep the shared queue in focus. No clutter,
            no visible agent layer, just a clean party workflow.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <FeatureTile title="Shared queue" value="Songs stay centered" />
          <FeatureTile title="Fast join" value="Room link or room ID" />
          <FeatureTile title="Quiet system" value="Agent stays invisible" />
        </div>
      </div>

      <Card>
        <CardContent className="space-y-8">
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold text-white">Start a room</h2>
            <p className="text-sm leading-6 text-slate-400">
              Create a new room or open an existing one. The backend flow stays exactly as
              before; only the UI shell changes.
            </p>
          </div>

          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              void onCreateRoom(roomName.trim() || "My Party");
            }}
          >
            <FieldLabel htmlFor="room-name" label="Room name" />
            <Input
              id="room-name"
              onChange={(event) => {
                setRoomName(event.target.value);
              }}
              placeholder="Rooftop Session"
              value={roomName}
            />
            <Button className="w-full gap-2" disabled={isLoading} size="lg" type="submit">
              <PlusCircle className="h-4 w-4" />
              {isLoading ? "Creating room..." : "Create room"}
            </Button>
          </form>

          <div className="flex items-center gap-4 text-xs uppercase tracking-[0.22em] text-slate-600">
            <div className="h-px flex-1 bg-white/8" />
            Join existing
            <div className="h-px flex-1 bg-white/8" />
          </div>

          <div className="space-y-4">
            <FieldLabel htmlFor="room-id" label="Room ID" />
            <Input
              id="room-id"
              onChange={(event) => {
                setRoomId(event.target.value);
              }}
              placeholder="Paste an existing room ID"
              value={roomId}
            />
            <Button
              className="w-full gap-2"
              disabled={isLoading || !roomId.trim()}
              onClick={() => {
                void onJoinRoom(roomId.trim());
              }}
              size="lg"
              variant="secondary"
            >
              <Link2 className="h-4 w-4" />
              Open room
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          {errorMessage ? (
            <p className="rounded-2xl border border-rose-400/12 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {errorMessage}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}

function FeatureTile({ title, value }: { title: string; value: string }): JSX.Element {
  return (
    <div className="rounded-[24px] border border-white/6 bg-white/[0.03] p-5">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 text-lg font-medium text-slate-100">{value}</p>
    </div>
  );
}

function FieldLabel({
  htmlFor,
  label,
}: {
  htmlFor: string;
  label: string;
}): JSX.Element {
  return (
    <label className="block text-sm font-medium text-slate-300" htmlFor={htmlFor}>
      {label}
    </label>
  );
}
