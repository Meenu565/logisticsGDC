import { motion } from "framer-motion";
import { Avatar } from "../ui/avatar";
import { ChatCard } from "./ChatCard";
import type { ChatMessage, DashboardState } from "../../types/dispatch";

export function MessageBubble({ message, dashboard }: { message: ChatMessage; dashboard: DashboardState }) {
  const isAssistant = message.role === "assistant";
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isAssistant ? "" : "flex-row-reverse"}`}
    >
      {isAssistant ? <Avatar initials="AI" className="mt-1" /> : <Avatar initials="ME" className="mt-1 bg-white/10" />}
      <div className={`max-w-[86%] ${isAssistant ? "" : "items-end"}`}>
        <div
          className={`rounded-3xl px-5 py-4 text-[15px] leading-7 shadow-soft ${
            isAssistant ? "bg-[#111827] text-slate-100" : "bg-blue-500 text-white"
          }`}
        >
          {message.content}
        </div>
        {message.cards?.map((card, index) => (
          <ChatCard card={card} dashboard={dashboard} key={`${card.title}-${index}`} />
        ))}
      </div>
    </motion.div>
  );
}
