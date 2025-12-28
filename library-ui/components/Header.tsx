"use client";

import { usePathname } from "next/navigation";
import Image from "next/image";
import { ModeToggle } from "@/components/ThemeToggle";
import { LogoutButton } from "@/components/LogoutButton";
import { BRANDING } from "@/lib/branding";

export function Header() {
  const pathname = usePathname();
  
  // Don't show header on login or offline pages
  if (pathname === "/login" || pathname === "/offline") {
    return null;
  }

  return (
    <header className="bg-card border-b border-border shadow-sm">
      <div className="px-4 sm:px-8 lg:px-24 py-4">
        <div className="flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="shrink-0 flex items-center gap-3">
            <div className="relative shrink-0">
              <Image
                src="/logo.svg"
                alt={BRANDING.name}
                width={40}
                height={40}
                className="rounded-lg"
              />
              {/* Subtle glow effect behind logo */}
              <div className="absolute inset-0 -z-10 bg-primary/20 blur-xl rounded-lg"></div>
            </div>
            <div className="flex flex-col justify-center min-h-[40px]">
              <h1 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent tracking-tight leading-tight">
                {BRANDING.name}
              </h1>
              <p className="text-[10px] md:text-xs text-muted-foreground leading-tight">
                {BRANDING.tagline}
              </p>
            </div>
          </div>

          {/* Theme Toggle and Logout */}
          <div className="shrink-0 flex items-center gap-2">
            <ModeToggle />
            <LogoutButton />
          </div>
        </div>
      </div>
    </header>
  );
}

