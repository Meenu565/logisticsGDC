import { motion } from "framer-motion";
import { Volume2 } from "lucide-react";
import { Avatar } from "../ui/avatar";
import { ChatCard } from "./ChatCard";
import type { ChatMessage, DashboardState } from "../../types/dispatch";

export function MessageBubble({
  message,
  dashboard,
  onReplayVoice,
}: {
  message: ChatMessage;
  dashboard: DashboardState;
  onReplayVoice?: (text: string) => void;
}) {
  const isAssistant = message.role === "assistant";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15 }}
      className={`flex gap-3 ${isAssistant ? "" : "flex-row-reverse"}`}
    >
      {isAssistant ? (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-stone-800 text-purple-300 border border-stone-700/60 text-[10px] font-semibold mt-1 shadow-sm">
          AI
        </div>
      ) : (
        <Avatar initials="ME" className="h-7 w-7 mt-1 bg-stone-800 text-stone-300 border border-stone-700/60 text-[10px]" />
      )}
      <div className={`max-w-[88%] ${isAssistant ? "" : "items-end"}`}>
        <div
          className={`group relative rounded-2xl px-4 py-3 text-[14px] leading-6 shadow-sm transition-all ${
            isAssistant
              ? "bg-[#181615] text-stone-200 border border-stone-800/80"
              : "bg-[#292524] text-stone-100 border border-stone-700/70"
          }`}
        >
          {message.content}

          {isAssistant && onReplayVoice && message.content && (
            <button
              type="button"
              onClick={() => onReplayVoice(message.content)}
              className="absolute bottom-2 right-2 rounded-full bg-stone-800/80 border border-stone-700/60 p-1 text-stone-400 opacity-0 transition-opacity hover:text-purple-300 hover:border-purple-400/40 group-hover:opacity-100"
              title="Speak this response (Aura)"
              aria-label="Replay audio"
            >
              <Volume2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {message.cards?.map((card, index) => (
          <ChatCard card={card} dashboard={dashboard} key={`${card.title}-${index}`} />
        ))}
      </div>
    </motion.div>
  );
}
