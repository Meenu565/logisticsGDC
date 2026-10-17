import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Radio, Sparkles, Truck } from "lucide-react";
import { DispatchMap } from "../components/map/DispatchMap";
import { ChatShell } from "../components/chat/ChatShell";
import { ContextPanel } from "../components/panels/ContextPanel";
import { fetchDashboardState } from "../services/dispatchApi";
import { useDispatchStore } from "../store/useDispatchStore";
import { Badge } from "../components/ui/badge";

export function DispatchWorkspace() {
  const hydrateContext = useDispatchStore((state) => state.hydrateContext);
  const { data: dashboard, error } = useQuery({
    queryKey: ["dashboard-state"],
    queryFn: fetchDashboardState,
    refetchInterval: 15000,
  });

  useEffect(() => {
    if (dashboard) hydrateContext(dashboard);
  }, [dashboard, hydrateContext]);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0c0a09] p-6 text-center">
        <div className="max-w-md rounded-3xl border border-stone-800 bg-[#161413] p-8 shadow-card">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-400 mb-4">
            <Radio className="h-6 w-6" />
          </div>
          <h2 className="text-base font-semibold text-stone-100">Backend Connection Error</h2>
          <p className="mt-2 text-sm leading-6 text-stone-400">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0c0a09]">
        <div className="flex items-center gap-3 text-stone-400 text-sm">
          <span className="h-2 w-2 animate-ping rounded-full bg-stone-300" />
          <span>Initializing workspace...</span>
        </div>
      </div>
    );
  }

  const activeDriverCount = dashboard.drivers.filter((d) => d.status === "available" || d.status === "on_route").length;
  const orderCount = dashboard.orders.length;

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[#0c0a09] text-stone-200">
      {/* ElevenLabs Style Top Bar */}
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-stone-800/80 px-6 backdrop-blur-md bg-[#0c0a09]/80 z-20">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-stone-950 font-bold text-xs shadow-sm">
              <span className="tracking-tighter">II</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[14px] font-semibold tracking-tight text-white flex items-center gap-2">
                ElevenLabs <span className="text-stone-500 font-normal">/</span> Dispatch Copilot
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-2 pl-4 border-l border-stone-800">
            <Badge variant="stone" className="text-[11px]">
              <Truck className="h-3 w-3 text-stone-400" />
              <span>{activeDriverCount} Drivers</span>
            </Badge>
            <Badge variant="stone" className="text-[11px]">
              <span>{orderCount} Orders</span>
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="lavender" className="hidden sm:inline-flex py-1 px-3">
            <Sparkles className="h-3 w-3 text-purple-300" />
            <span>Voice Agent Ready</span>
          </Badge>
          <div className="flex items-center gap-1.5 rounded-full border border-stone-800 bg-stone-900/60 px-3 py-1 text-xs text-stone-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span>Supabase Live</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Grid */}
      <main className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[minmax(300px,30%)_minmax(460px,46%)_minmax(280px,24%)]">
        <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }} className="min-h-[280px] lg:min-h-0">
          <DispatchMap dashboard={dashboard} />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} className="min-h-0">
          <ChatShell dashboard={dashboard} />
        </motion.div>
        <motion.div initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }} className="min-h-[280px] lg:min-h-0">
          <ContextPanel dashboard={dashboard} />
        </motion.div>
      </main>
    </div>
  );
}
