import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, CheckCircle2, CircleDashed } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { sendChatMessage, importOrders, resetWorkspace } from "../../services/dispatchApi";
import { useDispatchStore } from "../../store/useDispatchStore";
import type { DashboardState } from "../../types/dispatch";

const activitySteps = [
  "Understanding request",
  "Reading today's orders",
  "Finding available drivers",
  "Running optimization",
  "Comparing recommendations",
  "Updating dispatch memory",
  "Response ready",
];

export function ChatShell({ dashboard }: { dashboard: DashboardState }) {
  const queryClient = useQueryClient();
  const messages = useDispatchStore((state) => state.messages);
  const appendMessage = useDispatchStore((state) => state.appendMessage);
  const resetWorkspaceState = useDispatchStore((state) => state.resetWorkspaceState);
  const syncFromMessage = useDispatchStore((state) => state.syncFromMessage);
  const [activityIndex, setActivityIndex] = useState(0);
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  const chatMutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: (message) => {
      appendMessage(message);
      syncFromMessage(message, dashboard);
      queryClient.invalidateQueries({ queryKey: ["dashboard-state"] });
    },
  });

  const importMutation = useMutation({
    mutationFn: ({ file, mode }: { file: File; mode: "append" | "replace" }) => importOrders(file, mode),
    onSuccess: (message) => {
      appendMessage(message);
      syncFromMessage(message, dashboard);
      queryClient.invalidateQueries({ queryKey: ["dashboard-state"] });
    },
  });

  const resetMutation = useMutation({
    mutationFn: resetWorkspace,
    onSuccess: () => {
      resetWorkspaceState();
      queryClient.invalidateQueries({ queryKey: ["dashboard-state"] });
    },
  });

  const busy = chatMutation.isPending || importMutation.isPending || resetMutation.isPending;
  const error = chatMutation.error ?? importMutation.error ?? resetMutation.error;

  useEffect(() => {
    if (!busy) {
      setActivityIndex(0);
      return;
    }
    const interval = window.setInterval(() => {
      setActivityIndex((current) => Math.min(current + 1, activitySteps.length - 1));
    }, 420);
    return () => window.clearInterval(interval);
  }, [busy]);

  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, busy, activityIndex]);

  const handleSend = (content: string) => {
    appendMessage({ id: crypto.randomUUID(), role: "dispatcher", content, timestamp: "now" });
    chatMutation.mutate(content);
  };

  return (
    <section className="flex h-full min-w-0 flex-col rounded-[24px] border border-white/8 bg-[#080d18]">
      <div className="flex items-center gap-3 border-b border-white/8 px-5 py-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-500/16 text-blue-200">
          <Bot className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg font-semibold text-white">Operations copilot</h1>
          <p className="truncate text-sm text-slate-400">Ask, approve, reroute, and import directly from the conversation.</p>
        </div>
      </div>

      <div ref={scrollerRef} className="scrollbar-soft min-h-0 flex-1 space-y-5 overflow-y-auto px-5 py-5">
        {messages.map((message) => (
          <MessageBubble dashboard={dashboard} message={message} key={message.id} />
        ))}
        {messages.length === 0 && !busy && (
          <div className="flex h-full min-h-[360px] items-center justify-center text-center">
            <div>
              <div className="text-sm font-medium text-slate-300">No conversation yet</div>
              <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                Import orders or ask about the active dispatch session to begin.
              </p>
            </div>
          </div>
        )}
        {error && (
          <div className="ml-12 rounded-2xl border border-red-400/20 bg-red-500/10 p-4 text-sm text-red-100">
            {error.message}
          </div>
        )}
        <AnimatePresence>{busy && <ActivityTimeline activeIndex={activityIndex} />}</AnimatePresence>
      </div>

      <div className="p-4">
        <ChatInput
          onSend={handleSend}
          onImport={(file, mode) => importMutation.mutate({ file, mode })}
          onReset={() => resetMutation.mutate()}
          disabled={chatMutation.isPending}
        />
      </div>
    </section>
  );
}

function ActivityTimeline({ activeIndex }: { activeIndex: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      className="ml-12 rounded-2xl border border-blue-300/14 bg-blue-500/8 p-4"
    >
      <div className="text-sm font-medium text-blue-100">Dispatch intelligence is working</div>
      <div className="mt-3 space-y-2">
        {activitySteps.map((step, index) => {
          const complete = index < activeIndex || activeIndex === activitySteps.length - 1;
          const active = index === activeIndex && !complete;
          return (
            <div key={step} className="flex items-center gap-2 text-sm">
              {complete ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-300" />
              ) : (
                <CircleDashed className={`h-4 w-4 ${active ? "animate-spin text-blue-200" : "text-slate-600"}`} />
              )}
              <span className={complete || active ? "text-slate-200" : "text-slate-500"}>{step}</span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
