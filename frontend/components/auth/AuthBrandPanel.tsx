"use client";

import { motion } from "framer-motion";
import { BarChart2, Zap } from "lucide-react";
import { Logo } from "@/components/ui/logo";
import { BRANDING } from "@/lib/branding";

export function AuthBrandPanel() {
  return (
    <div className="hidden lg:flex flex-col justify-between w-1/2 p-12 bg-[#0f172a] text-white relative overflow-hidden financial-bg">
      {/* Top Branding */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="z-10"
      >
        <Logo 
          textClassName="text-white" 
          iconClassName="shadow-none bg-primary" 
        />
        <p className="text-slate-400 text-lg font-medium mt-2">
          {BRANDING.tagline}
        </p>
      </motion.div>

      {/* Feature Highlights */}
      <div className="z-10 mt-auto">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="space-y-6"
        >
          <div className="flex items-start gap-4">
            <div className="p-2 rounded-lg bg-slate-800/50 text-blue-400 mt-1">
              <BarChart2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-200">
                Deep Financial Analysis
              </h3>
              <p className="text-slate-400 mt-1">
                Instantly process complex financial statements and uncover hidden insights.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="p-2 rounded-lg bg-slate-800/50 text-emerald-400 mt-1">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-200">
                Real-time Valuation
              </h3>
              <p className="text-slate-400 mt-1">
                AI-driven intrinsic value modeling powered by consensus estimates.
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom Legal/Credit */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="z-10 mt-12 text-sm text-slate-500"
      >
        {BRANDING.copyright}
      </motion.div>
    </div>
  );
}
