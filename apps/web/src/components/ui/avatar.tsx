import { cn } from "../../lib/utils";

export function Avatar({ initials, className }: { initials: string; className?: string }) {
  return (
    <div
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/18 text-sm font-semibold text-blue-100 ring-1 ring-blue-300/20",
        className,
      )}
    >
      {initials}
    </div>
  );
}
