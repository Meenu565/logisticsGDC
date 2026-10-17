import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface BadgeProps {
  className?: string;
  children: ReactNode;
  variant?: "default" | "mint" | "lavender" | "peach" | "sky" | "stone";
}

export function Badge({ className, children, variant = "default" }: BadgeProps) {
  const variantStyles = {
    default: "border-stone-700/60 bg-stone-800/40 text-stone-300",
    stone: "border-stone-700/60 bg-stone-800/60 text-stone-300",
    mint: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    lavender: "border-purple-400/30 bg-purple-500/10 text-purple-200",
    peach: "border-orange-400/30 bg-orange-500/10 text-orange-200",
    sky: "border-sky-400/30 bg-sky-500/10 text-sky-200",
  }[variant];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium tracking-[0.03em]",
        variantStyles,
        className,
      )}
    >
      {children}
    </span>
  );
}
