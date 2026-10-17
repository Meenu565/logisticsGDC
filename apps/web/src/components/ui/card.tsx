import * as React from "react";
import { cn } from "../../lib/utils";

export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-2xl border border-stone-800/80 bg-[#161413] text-stone-200 shadow-card transition-all duration-200",
        className,
      )}
      {...props}
    />
  ),
);

Card.displayName = "Card";
