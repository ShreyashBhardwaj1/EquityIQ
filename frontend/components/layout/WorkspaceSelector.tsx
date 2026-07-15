"use client";

import { useState } from "react";
import { Briefcase, Check, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Mock data until real API is wired
const workspaces = [
  { id: "1", name: "Personal Workspace" },
  { id: "2", name: "Acme Corp Analysis" },
];

export function WorkspaceSelector() {
  const [activeWorkspace, setActiveWorkspace] = useState(workspaces[0]);

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
            <span className="truncate">{activeWorkspace.name}</span>
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
            onClick={() => setActiveWorkspace(workspace)}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="truncate">{workspace.name}</span>
            {activeWorkspace.id === workspace.id && (
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
