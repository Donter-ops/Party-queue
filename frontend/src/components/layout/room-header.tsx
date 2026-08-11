import { Copy, LogOut } from "lucide-react";
import type { JSX } from "react";

import { Button } from "../ui/button";
import { AgentNotification } from "../ui/notification";

interface RoomHeaderProps {
  isRefreshing: boolean;
  memberCount: number;
  roomName: string;
  onCopyShareLink: () => Promise<void>;
  onLeaveRoom: () => void;
}

export function RoomHeader({
  isRefreshing,
  memberCount,
  roomName,
  onCopyShareLink,
  onLeaveRoom,
}: RoomHeaderProps): JSX.Element {
  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-slate-500">
            Listening together
          </p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">{roomName}</h1>
          <p className="text-sm text-slate-400">
            {memberCount} member{memberCount !== 1 ? "s" : ""}
            {isRefreshing ? " | syncing" : ""}
          </p>
        </div>

        {/* Hidden by default so future agent signals can surface without changing the main layout. */}
        <AgentNotification message="Matching song..." visible={false} />
      </div>

      <div className="flex flex-wrap gap-3">
        <Button
          className="gap-2"
          onClick={() => {
            void onCopyShareLink();
          }}
          variant="outline"
        >
          <Copy className="h-4 w-4" />
          Copy room link
        </Button>
        <Button className="gap-2" onClick={onLeaveRoom} variant="ghost">
          <LogOut className="h-4 w-4" />
          Leave room
        </Button>
      </div>
    </div>
  );
}
