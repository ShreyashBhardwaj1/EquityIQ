"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";
import { Sun, Moon, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AppearanceSettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Appearance</h2>
        <p className="text-muted-foreground mt-1">
          Customize how EquityIQ looks on your device.
        </p>
      </div>

      <Card className="bg-background/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle>Theme Preferences</CardTitle>
          <CardDescription>
            Select your preferred color theme. The atmospheric background adapts automatically.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            
            <button 
              onClick={() => setTheme("light")}
              className={cn(
                "flex flex-col items-center justify-center p-4 border-2 rounded-xl transition-all w-32",
                theme === "light" ? "border-primary bg-primary/5" : "border-border/50 hover:border-primary/50"
              )}
            >
              <Sun className={cn("w-6 h-6 mb-2", theme === "light" ? "text-primary" : "text-muted-foreground")} />
              <span className="text-sm font-medium">Light</span>
            </button>

            <button 
              onClick={() => setTheme("dark")}
              className={cn(
                "flex flex-col items-center justify-center p-4 border-2 rounded-xl transition-all w-32",
                theme === "dark" ? "border-primary bg-primary/5" : "border-border/50 hover:border-primary/50"
              )}
            >
              <Moon className={cn("w-6 h-6 mb-2", theme === "dark" ? "text-primary" : "text-muted-foreground")} />
              <span className="text-sm font-medium">Dark</span>
            </button>

            <button 
              onClick={() => setTheme("system")}
              className={cn(
                "flex flex-col items-center justify-center p-4 border-2 rounded-xl transition-all w-32",
                theme === "system" ? "border-primary bg-primary/5" : "border-border/50 hover:border-primary/50"
              )}
            >
              <Monitor className={cn("w-6 h-6 mb-2", theme === "system" ? "text-primary" : "text-muted-foreground")} />
              <span className="text-sm font-medium">System</span>
            </button>

          </div>
        </CardContent>
      </Card>
    </div>
  );
}
