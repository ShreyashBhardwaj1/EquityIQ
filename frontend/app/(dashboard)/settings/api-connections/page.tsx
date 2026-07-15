"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Link2 } from "lucide-react";

export default function ApiConnectionsPage() {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">API Connections</h2>
        <p className="text-muted-foreground mt-1">
          Manage integrations with external financial systems.
        </p>
      </div>

      <Card className="bg-background/50 backdrop-blur-sm">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-md">
              <Link2 className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>OpenAI API Key</CardTitle>
              <CardDescription>
                Provide your own API key for LLM operations to bypass usage limits.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 max-w-lg">
            <Label htmlFor="api-key">Secret Key</Label>
            <Input id="api-key" type="password" placeholder="sk-..." />
            <p className="text-xs text-muted-foreground">Key is encrypted at rest and never shared.</p>
          </div>
        </CardContent>
        <CardFooter className="border-t border-border/50 bg-muted/20 px-6 py-4">
          <Button>Save Configuration</Button>
        </CardFooter>
      </Card>
    </div>
  );
}
