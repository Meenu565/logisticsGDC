import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMinutes(seconds: number) {
  return `${Math.round(seconds / 60)} min`;
}

export function formatDistance(meters: number) {
  return `${(meters / 1000).toFixed(1)} km`;
}

