import Link from "next/link";
import { CardFooter } from "@/components/ui/card";

interface AuthFooterProps {
  text: string;
  linkText: string;
  href: string;
}

export function AuthFooter({ text, linkText, href }: AuthFooterProps) {
  return (
    <CardFooter className="flex justify-center">
      <div className="text-sm text-muted-foreground text-center">
        {text}{" "}
        <Link
          href={href}
          className="font-medium text-primary hover:text-primary/80 transition-colors underline underline-offset-4"
        >
          {linkText}
        </Link>
      </div>
    </CardFooter>
  );
}
