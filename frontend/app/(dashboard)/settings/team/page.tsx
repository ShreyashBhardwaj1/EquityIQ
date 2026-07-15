"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { UserPlus, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function TeamSettingsPage() {
  const members = [
    { id: 1, name: "John Doe", email: "john.doe@equityiq.com", role: "Owner" },
    { id: 2, name: "Jane Smith", email: "jane.smith@equityiq.com", role: "Admin" },
    { id: 3, name: "Alex Johnson", email: "alex.j@equityiq.com", role: "Viewer" },
  ];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Team Members</h2>
          <p className="text-muted-foreground mt-1">
            Manage who has access to this workspace.
          </p>
        </div>
        <Button className="gap-2">
          <UserPlus className="w-4 h-4" />
          Invite Member
        </Button>
      </div>

      <Card className="bg-background/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle>Active Members</CardTitle>
          <CardDescription>
            Users with active access to intelligence data.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-border/50 border rounded-lg">
            {members.map((m) => (
              <div key={m.id} className="flex items-center justify-between p-4 hover:bg-muted/30 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10 text-primary">
                    <User className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{m.name}</div>
                    <div className="text-xs text-muted-foreground">{m.email}</div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <Badge variant={m.role === "Owner" ? "default" : "secondary"}>
                    {m.role}
                  </Badge>
                  <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-destructive">
                    Remove
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
