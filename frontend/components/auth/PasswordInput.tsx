"use client";

import * as React from "react";
import { Eye, EyeOff } from "lucide-react";
import { Input, type InputProps } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface PasswordInputProps extends Omit<InputProps, "type"> {
  showStrengthIndicator?: boolean;
}

const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, showStrengthIndicator = false, value, ...props }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const passwordValue = (value as string) || "";

    const calculateStrength = (pass: string) => {
      let strength = 0;
      if (pass.length > 0) strength += 25;
      if (pass.length > 7) strength += 25;
      if (pass.match(/[A-Z]/) && pass.match(/[a-z]/)) strength += 25;
      if (pass.match(/[0-9]/) || pass.match(/[^A-Za-z0-9]/)) strength += 25;
      return strength;
    };

    const strength = calculateStrength(passwordValue);

    const getStrengthLabel = (s: number) => {
      if (s === 0) return "";
      if (s <= 25) return "Weak";
      if (s <= 50) return "Fair";
      if (s <= 75) return "Good";
      return "Strong";
    };

    const getStrengthColor = (s: number) => {
      if (s <= 25) return "bg-destructive text-destructive";
      if (s <= 50) return "bg-amber-500 text-amber-500";
      if (s <= 75) return "bg-emerald-400 text-emerald-400";
      return "bg-emerald-600 text-emerald-600";
    };

    return (
      <div className="space-y-2">
        <div className="relative">
          <Input
            type={showPassword ? "text" : "password"}
            className={cn("pr-10 input-glow", className)}
            ref={ref}
            value={value}
            {...props}
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent text-muted-foreground hover:text-foreground"
            onClick={() => setShowPassword((prev) => !prev)}
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4" aria-hidden="true" />
            )}
            <span className="sr-only">
              {showPassword ? "Hide password" : "Show password"}
            </span>
          </Button>
        </div>

        {showStrengthIndicator && passwordValue.length > 0 && (
          <div className="mt-2 space-y-1.5">
            <div className="flex gap-1 h-1 w-full">
              {[25, 50, 75, 100].map((threshold) => (
                <div
                  key={threshold}
                  className={cn(
                    "strength-bar flex-1",
                    strength >= threshold
                      ? getStrengthColor(strength).split(" ")[0]
                      : "bg-muted"
                  )}
                />
              ))}
            </div>
            <div className="flex justify-end">
              <span
                className={cn(
                  "text-xs font-medium transition-colors duration-300",
                  getStrengthColor(strength).split(" ")[1]
                )}
              >
                {getStrengthLabel(strength)}
              </span>
            </div>
          </div>
        )}
      </div>
    );
  }
);
PasswordInput.displayName = "PasswordInput";

export { PasswordInput };
