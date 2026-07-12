import * as React from "react";

import { cn } from "../../lib/utils";

export function Badge({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>): React.JSX.Element {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-white/8 bg-white/6 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-slate-300",
        className,
      )}
      {...props}
    />
  );
}
