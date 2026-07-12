import type { JSX, ReactNode } from "react";

import { TopNavigation } from "./top-navigation";

interface ApplicationShellProps {
  children: ReactNode;
  memberCount?: number;
  roomName?: string;
}

export function ApplicationShell({
  children,
  memberCount,
  roomName,
}: ApplicationShellProps): JSX.Element {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top,rgba(120,119,198,0.12),transparent_24%),radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.12),transparent_20%),linear-gradient(180deg,#020617_0%,#0f172a_100%)]" />
      <TopNavigation memberCount={memberCount} roomName={roomName} />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8 lg:py-12">
        {children}
      </main>
    </div>
  );
}
