"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface AuthCardProps {
  children: ReactNode;
  className?: string;
}

export function AuthCard({ children, className }: AuthCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={cn("w-full max-w-md mx-auto", className)}
    >
      <Card className="glass-card w-full border-border/40 shadow-xl dark:shadow-none p-2 sm:p-4">
        {children}
      </Card>
    </motion.div>
  );
}
