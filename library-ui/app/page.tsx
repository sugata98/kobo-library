"use client";

import { useState, useEffect } from "react";
import BookList from "@/components/BookList";
import { ModeToggle } from "@/components/ThemeToggle";
import { Search } from "lucide-react";
import Image from "next/image";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group";
import { BRANDING } from "@/lib/branding";

export default function Home() {
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
    }, 300); // 300ms delay

    return () => clearTimeout(timer);
  }, [searchQuery]);

  return (
    <main className="min-h-screen bg-background text-foreground">
      {/* Header with Logo, Search, and Theme Toggle */}
      <header className="sticky top-0 z-50 bg-card border-b border-border shadow-sm">
        <div className="px-4 sm:px-8 lg:px-24 py-4">
          {/* Desktop Layout: Logo | Search | Toggle */}
          {/* Mobile Layout: Logo/Toggle stacked, Search below */}
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            {/* Top Row: Logo and Theme Toggle */}
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

              {/* Theme Toggle - visible on mobile */}
              <div className="shrink-0 md:hidden">
                <ModeToggle />
              </div>
            </div>

            {/* Search Bar - Full width on mobile, right-aligned on desktop */}
            <div className="w-full md:w-auto md:flex-1 md:max-w-md md:ml-auto md:mr-4">
              <InputGroup>
                <InputGroupAddon>
                  <Search />
                </InputGroupAddon>
                <InputGroupInput
                  type="text"
                  placeholder={BRANDING.ui.searchPlaceholder}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </InputGroup>
            </div>

            {/* Theme Toggle - hidden on mobile, visible on desktop */}
            <div className="shrink-0 hidden md:block">
              <ModeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="px-4 sm:px-8 lg:px-24 py-6">
        <BookList searchQuery={debouncedSearchQuery} />
      </div>
    </main>
  );
}
