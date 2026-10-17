import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-full text-[14px] font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-stone-400 disabled:pointer-events-none disabled:opacity-40 select-none",
  {
    variants: {
      variant: {
        default:
          "bg-white text-stone-950 shadow-sm hover:bg-stone-100 active:scale-[0.98]",
        secondary:
          "bg-stone-800/60 text-stone-200 border border-stone-700/60 hover:bg-stone-800 hover:text-white active:scale-[0.98]",
        ghost:
          "text-stone-400 hover:text-stone-100 hover:bg-stone-800/40",
        outline:
          "border border-stone-700/60 bg-transparent text-stone-200 hover:bg-stone-800/50 hover:text-white hover:border-stone-600 active:scale-[0.98]",
        pill:
          "bg-white/10 text-stone-200 border border-white/10 hover:bg-white/15 hover:text-white",
        danger:
          "bg-red-500/12 text-red-300 border border-red-500/20 hover:bg-red-500/20",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-6 text-[15px]",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  ),
);

Button.displayName = "Button";
