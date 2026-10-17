import { motion } from "framer-motion";

interface VoiceVisualizerProps {
  mode: "listening" | "speaking" | "idle";
}

const pastelColors = [
  "#a7e5d3", // mint
  "#c8b8e0", // lavender
  "#f4c5a8", // peach
  "#a8c8e8", // sky
  "#e8b8c4", // rose
  "#a7e5d3", // mint
];

export function VoiceVisualizer({ mode }: VoiceVisualizerProps) {
  if (mode === "idle") return null;

  const isSpeaking = mode === "speaking";

  return (
    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-stone-900/80 border border-stone-800">
      <div className="flex items-center gap-[3px] h-4">
        {pastelColors.map((color, i) => (
          <motion.span
            key={i}
            className="w-[2.5px] rounded-full"
            style={{ backgroundColor: color }}
            animate={{
              height: isSpeaking ? [4, 16, 8, 18, 4] : [4, 12, 6, 14, 4],
            }}
            transition={{
              repeat: Infinity,
              repeatType: "reverse",
              duration: 0.5 + (i % 3) * 0.12,
              delay: i * 0.06,
            }}
          />
        ))}
      </div>
      <span className="text-[11px] font-medium tracking-wide text-stone-300">
        {isSpeaking ? "Speaking" : "Listening"}
      </span>
    </div>
  );
}
