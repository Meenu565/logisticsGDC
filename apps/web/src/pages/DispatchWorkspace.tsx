import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { DispatchMap } from "../components/map/DispatchMap";
import { ChatShell } from "../components/chat/ChatShell";
import { ContextPanel } from "../components/panels/ContextPanel";
import { fetchDashboardState } from "../services/dispatchApi";
import { useDispatchStore } from "../store/useDispatchStore";

export function DispatchWorkspace() {
  const hydrateContext = useDispatchStore((state) => state.hydrateContext);
  const { data: dashboard, error } = useQuery({
    queryKey: ["dashboard-state"],
    queryFn: fetchDashboardState,
  });

  useEffect(() => {
    if (dashboard) hydrateContext(dashboard);
  }, [dashboard, hydrateContext]);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center bg-[#050913] p-6 text-center">
        <div>
          <div className="text-sm font-semibold text-white">Backend connection failed</div>
          <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return <div className="h-full bg-[#050913]" />;
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      
      <main className="grid min-h-0 flex-1 grid-cols-1 gap-5 p-5 lg:grid-cols-[minmax(280px,28%)_minmax(480px,52%)_minmax(280px,20%)]">
        <motion.div initial={{ opacity: 0, x: -18 }} animate={{ opacity: 1, x: 0 }} className="min-h-[280px] lg:min-h-0">
          <DispatchMap dashboard={dashboard} />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="min-h-0">
          <ChatShell dashboard={dashboard} />
        </motion.div>
        <motion.div initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} className="min-h-[280px] lg:min-h-0">
          <ContextPanel dashboard={dashboard} />
        </motion.div>
      </main>
    </div>
  );
}
