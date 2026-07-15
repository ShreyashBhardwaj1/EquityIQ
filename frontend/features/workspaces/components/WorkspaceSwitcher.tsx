"use client";

import { useWorkspacesList, useSwitchWorkspace } from "../hooks/use-workspaces";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Briefcase, Loader2 } from "lucide-react";
import { useState } from "react";

export function WorkspaceSwitcher() {
  const { data: workspaces, isLoading } = useWorkspacesList();
  const switchMutation = useSwitchWorkspace();
  
  // We mock the currently active ID since we don't have a global context.
  // In a real app, this would be determined by a token claim or cookie.
  // For the UI, we'll default to the first workspace.
  const [activeId, setActiveId] = useState<string>("");

  const handleSwitch = async (id: string) => {
    setActiveId(id);
    await switchMutation.mutateAsync(id);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground w-full">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Loading workspace...</span>
      </div>
    );
  }

  if (!workspaces || workspaces.length === 0) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground w-full">
        <Briefcase className="w-4 h-4" />
        <span>No Workspaces</span>
      </div>
    );
  }

  // Set default if none selected yet
  const displayId = activeId || workspaces[0]?.id;

  return (
    <div className="w-full">
      <Select value={displayId} onValueChange={handleSwitch}>
        <SelectTrigger className="w-full bg-background/50 border-border/50 hover:bg-muted/50 transition-colors h-10">
          <div className="flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-primary" />
            <span className="truncate max-w-[140px] text-left">
              {workspaces.find(w => w.id === displayId)?.name || "Select Workspace"}
            </span>
          </div>
        </SelectTrigger>
        <SelectContent>
          {workspaces.map(w => (
            <SelectItem key={w.id} value={w.id}>
              {w.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
