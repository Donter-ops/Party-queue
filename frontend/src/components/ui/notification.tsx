import type { JSX } from "react";
import { Sparkles } from "lucide-react";

interface NotificationProps {
  message: string;
  visible?: boolean;
}

export function AgentNotification({
  message,
  visible = false,
}: NotificationProps): JSX.Element | null {
  if (!visible) {
    return null;
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-sky-400/14 bg-sky-400/10 px-4 py-2 text-sm text-sky-100 shadow-[0_12px_48px_rgba(14,165,233,0.18)]">
      <Sparkles className="h-4 w-4" />
      <span>{message}</span>
    </div>
  );
}
