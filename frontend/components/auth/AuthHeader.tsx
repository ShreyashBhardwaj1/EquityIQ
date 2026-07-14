import { CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Logo } from "@/components/ui/logo";

interface AuthHeaderProps {
  title: string;
  description: string;
}

export function AuthHeader({ title, description }: AuthHeaderProps) {
  return (
    <CardHeader className="space-y-3 pb-6 text-center">
      <div className="flex justify-center mb-2 lg:hidden">
        <Logo showText={false} />
      </div>
      <CardTitle className="text-2xl font-semibold tracking-tight">
        {title}
      </CardTitle>
      <CardDescription className="text-sm text-muted-foreground">
        {description}
      </CardDescription>
    </CardHeader>
  );
}
