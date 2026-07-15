"use client";

import { motion } from "framer-motion";
import { BarChart2, Zap } from "lucide-react";
import { Logo } from "@/components/ui/logo";
import { BRANDING } from "@/lib/branding";

export function AuthBrandPanel() {
  return (
    <div className="hidden lg:flex flex-col justify-between w-[45%] p-12 bg-slate-950/40 text-white relative overflow-hidden backdrop-blur-sm">
      {/* Top Branding */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="z-10"
      >
        <Logo 
          textClassName="text-white text-2xl font-bold tracking-tight" 
          iconClassName="shadow-lg bg-blue-600 border-none" 
        />
        <h2 className="text-3xl font-semibold mt-12 leading-tight">
          Financial Intelligence Platform
        </h2>
        <p className="text-slate-400 text-lg mt-4 max-w-md">
          Institutional-grade financial intelligence. Built for modern equity analysis and real-time valuation.
        </p>
      </motion.div>

      {/* Decorative Node Network/Chart Graphic Placeholder */}
      <div className="z-10 mt-auto mb-16 relative h-64 w-full">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="absolute inset-0 bg-gradient-to-tr from-blue-600/20 to-transparent rounded-2xl border border-white/5 backdrop-blur-sm"
        />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="absolute bottom-6 left-6 right-6 h-32 bg-gradient-to-t from-blue-500/10 to-transparent border-t border-blue-500/20"
        >
          {/* Subtle line chart representation */}
          <svg className="w-full h-full opacity-50" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path d="M0,100 L0,50 C20,50 30,80 50,60 C70,40 80,20 100,10 L100,100 Z" fill="url(#grad)" />
            <path d="M0,50 C20,50 30,80 50,60 C70,40 80,20 100,10" fill="none" stroke="#3b82f6" strokeWidth="2" />
            <defs>
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
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
