"use client";

import { useState } from "react";
import { Briefcase, Check, ChevronsUpDown, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useWorkspacesList, useSwitchWorkspace } from "@/features/workspaces/hooks/use-workspaces";
import { Workspace } from "@/features/workspaces/types";

export function WorkspaceSelector() {
  const { data: workspaces, isLoading } = useWorkspacesList();
  const switchMutation = useSwitchWorkspace();

  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>("");

  const displayId = activeWorkspaceId || workspaces?.[0]?.id;
  const activeWorkspace = workspaces?.find(w => w.id === displayId);

  const handleSwitch = async (workspace: Workspace) => {
    setActiveWorkspaceId(workspace.id);
    await switchMutation.mutateAsync(workspace.id);
  };

  if (isLoading) {
    return (
      <Button variant="ghost" size="sm" className="h-8 w-full justify-between px-2 text-sm font-normal text-muted-foreground">
        <div className="flex items-center gap-2 truncate">
          <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
          <span>Loading...</span>
        </div>
      </Button>
    );
  }

  if (!workspaces || workspaces.length === 0) {
    return (
      <Button variant="ghost" size="sm" className="h-8 w-full justify-between px-2 text-sm font-normal text-muted-foreground">
        <div className="flex items-center gap-2 truncate">
          <Briefcase className="h-4 w-4 shrink-0" />
          <span>No Workspaces</span>
        </div>
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-full justify-between px-2 text-sm font-normal text-muted-foreground hover:text-foreground"
        >
          <div className="flex items-center gap-2 truncate">
            <Briefcase className="h-4 w-4 shrink-0" />
            <span className="truncate">{activeWorkspace?.name || "Select Workspace"}</span>
          </div>
          <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[200px]">
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          Workspaces
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {workspaces.map((workspace) => (
          <DropdownMenuItem
            key={workspace.id}
            onClick={() => handleSwitch(workspace)}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="truncate">{workspace.name}</span>
            {displayId === workspace.id && (
              <Check className="h-4 w-4 text-primary shrink-0" />
            )}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem className="cursor-pointer text-primary">
          + Create Workspace
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
