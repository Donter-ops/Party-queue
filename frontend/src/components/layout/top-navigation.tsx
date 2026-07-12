import type { JSX } from "react";
import { Users } from "lucide-react";

import { Badge } from "../ui/badge";
import { BrandMark } from "./brand-mark";

interface TopNavigationProps {
  memberCount?: number;
  roomName?: string;
}

export function TopNavigation({
  memberCount = 0,
  roomName = "No room selected",
}: TopNavigationProps): JSX.Element {
  return (
    <header className="sticky top-0 z-20 border-b border-white/6 bg-slate-950/72 backdrop-blur-2xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <BrandMark />

        <div className="flex items-center gap-3">
          <Badge className="hidden sm:inline-flex">{roomName}</Badge>
          <Badge className="gap-2">Zurück</Badge>
          <Badge className="gap-2">
            <Users className="h-3.5 w-3.5" />
            {memberCount} members
          </Badge>
        </div>
      </div>
    </header>
  );
}
