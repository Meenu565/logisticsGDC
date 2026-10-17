import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, CircleDashed, Sparkles, Volume2, VolumeX } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { VoiceVisualizer } from "./VoiceVisualizer";
import { sendChatMessage, importOrders, resetWorkspace, synthesizeVoiceSpeech, fetchVoiceStatus } from "../../services/dispatchApi";
import { useDispatchStore } from "../../store/useDispatchStore";
import type { DashboardState } from "../../types/dispatch";
import { Button } from "../ui/button";

const activitySteps = [
  "Understanding dispatcher intent",
  "Analyzing active order constraints",
  "Checking driver shifts & locations",
  "Google OR-Tools solver running",
  "Calculating OSRM route geometries",
  "Dispatch plan & voice response ready",
];

export function ChatShell({ dashboard }: { dashboard: DashboardState }) {
  const queryClient = useQueryClient();
  const messages = useDispatchStore((state) => state.messages);
  const appendMessage = useDispatchStore((state) => state.appendMessage);
  const resetWorkspaceState = useDispatchStore((state) => state.resetWorkspaceState);
  const syncFromMessage = useDispatchStore((state) => state.syncFromMessage);
  const [activityIndex, setActivityIndex] = useState(0);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [speaking, setSpeaking] = useState(false);
  const [voiceModel, setVoiceModel] = useState("Aura Asteria");

  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetchVoiceStatus().then((status) => {
      if (status.voice_model) {
        setVoiceModel(status.voice_model.replace("aura-", "Aura ").replace("-en", ""));
      }
    });
  }, []);

  const stopSpeaking = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setSpeaking(false);
  };

  const playVoiceResponse = async (text: string) => {
    if (!voiceEnabled || !text.trim()) return;
    try {
      stopSpeaking();
      const audioBlob = await synthesizeVoiceSpeech(text);
      if (audioBlob.size > 0) {
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.onplay = () => setSpeaking(true);
        audio.onended = () => {
          setSpeaking(false);
          audioRef.current = null;
          URL.revokeObjectURL(audioUrl);
        };
        audio.onerror = () => {
          setSpeaking(false);
          audioRef.current = null;
        };
        await audio.play();
      }
    } catch (err) {
      console.warn("Could not play voice synthesis response:", err);
      setSpeaking(false);
    }
  };

  const chatMutation = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: (message) => {
      appendMessage(message);
      syncFromMessage(message, dashboard);
      queryClient.invalidateQueries({ queryKey: ["dashboard-state"] });
      if (message.content) {
        playVoiceResponse(message.content);
      }
    },
  });

  const importMutation = useMutation({
    mutationFn: ({ file, mode }: { file: File; mode: "append" | "replace" }) => importOrders(file, mode),
    onSuccess: (message) => {
      appendMessage(message);
      syncFromMessage(message, dashboard);
      queryClient.invalidateQueries({ queryKey: ["dashboard-state"] });
      if (message.content) {
        playVoiceResponse(message.content);
      }
    },
  });

  const resetMutation = useMutation({
    mutationFn: resetWorkspace,
    onSuccess: () => {
      resetWorkspaceState();
      queryClient.invalidateQueries({ queryKey: ["dashboard-state"] });
      stopSpeaking();
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
    }, 450);
    return () => window.clearInterval(interval);
  }, [busy]);

  useEffect(() => {
    scrollerRef.current?.scrollTo({ top: scrollerRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, busy, activityIndex]);

  const handleSend = (content: string) => {
    stopSpeaking();
    appendMessage({ id: crypto.randomUUID(), role: "dispatcher", content, timestamp: "now" });
    chatMutation.mutate(content);
  };

  return (
    <section className="flex h-full min-w-0 flex-col rounded-3xl border border-stone-800/80 bg-[#141211] shadow-card overflow-hidden">
      {/* Editorial Header */}
      <div className="flex items-center justify-between border-b border-stone-800/80 px-5 py-3.5 bg-[#171513]">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-stone-800 text-stone-200 border border-stone-700/60 shadow-sm">
            <Sparkles className="h-4 w-4 text-purple-300" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-[14px] font-medium tracking-tight text-stone-100">Operations Copilot</h2>
              <span className="hidden sm:inline-flex rounded-full bg-stone-800/80 border border-stone-700/60 px-2 py-0.5 text-[10px] font-medium text-stone-400">
                {voiceModel}
              </span>
            </div>
            <p className="truncate text-xs text-stone-400">Conversational route planning & voice assignment</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {speaking && <VoiceVisualizer mode="speaking" />}
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => {
              if (speaking) stopSpeaking();
              setVoiceEnabled(!voiceEnabled);
            }}
            className={`h-8 px-3 text-xs gap-1.5 transition-all ${
              voiceEnabled
                ? "bg-stone-800 text-stone-200 border-stone-700/80 hover:bg-stone-700"
                : "bg-transparent text-stone-500 border-stone-800 hover:text-stone-300"
            }`}
            title={voiceEnabled ? "Voice Output Active (Aura)" : "Voice Output Muted"}
          >
            {voiceEnabled ? <Volume2 className="h-3.5 w-3.5 text-purple-300" /> : <VolumeX className="h-3.5 w-3.5" />}
            <span className="font-normal">{voiceEnabled ? "Voice On" : "Muted"}</span>
          </Button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div ref={scrollerRef} className="scrollbar-soft min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {messages.map((message) => (
          <MessageBubble
            dashboard={dashboard}
            message={message}
            key={message.id}
            onReplayVoice={(text) => playVoiceResponse(text)}
          />
        ))}

        {messages.length === 0 && !busy && (
          <div className="flex h-full min-h-[300px] flex-col items-center justify-center text-center p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-stone-800/80 border border-stone-700/60 text-purple-300 mb-3 shadow-glow">
              <Sparkles className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-medium text-stone-200">Ready to dispatch</h3>
            <p className="mt-1.5 max-w-xs text-xs leading-5 text-stone-400">
              Import orders, ask about driver capacities, or click the microphone to speak a command.
            </p>
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-3.5 text-xs text-red-200">
            {error.message}
          </div>
        )}

        <AnimatePresence>{busy && <ActivityTimeline activeIndex={activityIndex} />}</AnimatePresence>
      </div>

      {/* Input Form */}
      <div className="p-3 bg-[#110f0e] border-t border-stone-800/80">
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      className="rounded-2xl border border-stone-800 bg-[#191614] p-3.5 shadow-sm"
    >
      <div className="text-xs font-medium text-purple-200 flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-purple-400 animate-pulse" />
        <span>Optimization in progress</span>
      </div>
      <div className="mt-2.5 space-y-1.5">
        {activitySteps.map((step, index) => {
          const complete = index < activeIndex || activeIndex === activitySteps.length - 1;
          const active = index === activeIndex && !complete;
          return (
            <div key={step} className="flex items-center gap-2 text-xs">
              {complete ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <CircleDashed className={`h-3.5 w-3.5 ${active ? "animate-spin text-purple-300" : "text-stone-600"}`} />
              )}
              <span className={complete || active ? "text-stone-300" : "text-stone-600"}>{step}</span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
