import { ReactNode } from "react";
import { AuthBrandPanel } from "@/components/auth/AuthBrandPanel";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen bg-surface-1 overflow-hidden">
      {/* Left Panel: Decorative brand panel (hidden on mobile) */}
      <AuthBrandPanel />

      {/* Right Panel: Auth forms */}
      <div className="flex flex-col flex-1 relative h-full overflow-y-auto overflow-x-hidden">
        <div className="absolute top-4 right-4 z-50">
          <ThemeToggle />
        </div>
        
        <main className="flex-1 flex items-center justify-center p-4 sm:p-8 min-h-full">
          <div className="w-full max-w-[420px]">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
