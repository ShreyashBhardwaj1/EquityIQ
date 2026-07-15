"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function WorkspaceSettingsPage() {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Workspace Settings</h2>
        <p className="text-muted-foreground mt-1">
          Manage the configuration and lifecycle of your current active workspace.
        </p>
      </div>

      <Card className="bg-background/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle>Workspace Profile</CardTitle>
          <CardDescription>
            Update the workspace name and internal identifiers.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 max-w-sm">
            <Label htmlFor="ws-name">Workspace Name</Label>
            <Input id="ws-name" defaultValue="Acme Corp Intelligence" />
          </div>
        </CardContent>
        <CardFooter className="border-t border-border/50 bg-muted/20 px-6 py-4">
          <Button>Save Changes</Button>
        </CardFooter>
      </Card>

      <Card className="bg-destructive/5 border-destructive/20 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>
            Irreversible actions for this workspace.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive" className="mb-4 bg-destructive/10 border-destructive/20">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Archive Workspace</AlertTitle>
            <AlertDescription>
              Archiving a workspace will disable access for all members. 
              Historical data will be retained for 30 days before permanent deletion.
            </AlertDescription>
          </Alert>
          <Button variant="destructive">Archive Workspace</Button>
        </CardContent>
      </Card>
    </div>
  );
}
