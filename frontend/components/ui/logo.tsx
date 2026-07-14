import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { BRANDING } from "@/lib/branding";

interface LogoProps {
  className?: string;
  iconClassName?: string;
  textClassName?: string;
  showText?: boolean;
}

export function Logo({
  className,
  iconClassName,
  textClassName,
  showText = true,
}: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "w-8 h-8 rounded bg-primary flex items-center justify-center shadow-glow-sm",
          iconClassName
        )}
      >
        <TrendingUp className="w-5 h-5 text-white" />
      </div>
      {showText && (
        <span
          className={cn("text-2xl font-bold tracking-tight", textClassName)}
        >
          {BRANDING.name}
        </span>
      )}
    </div>
  );
}
