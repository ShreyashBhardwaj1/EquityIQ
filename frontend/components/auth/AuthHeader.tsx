import { CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Logo } from "@/components/ui/logo";

interface AuthHeaderProps {
  title: string;
  description: string;
}

export function AuthHeader({ title, description }: AuthHeaderProps) {
  return (
    <CardHeader className="space-y-4 pb-8 text-center">
      <div className="flex justify-center mb-6 lg:hidden">
        <Logo showText={false} />
      </div>
      <CardTitle className="text-3xl font-bold tracking-tight">
        {title}
      </CardTitle>
      <CardDescription className="text-base text-muted-foreground">
        {description}
      </CardDescription>
    </CardHeader>
  );
}
