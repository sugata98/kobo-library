"use client";

import { useState, useEffect } from "react";
import BookList from "@/components/BookList";
import { ModeToggle } from "@/components/ThemeToggle";
import { Search } from "lucide-react";
import Image from "next/image";
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
          <div className="flex items-center justify-between gap-4">
            {/* Logo - Left */}
            <div className="shrink-0 flex items-center gap-3">
              <Image
                src="/logo.svg"
                alt={BRANDING.name}
                width={40}
                height={40}
                className="rounded-lg"
              />
              <h1 className="text-2xl font-bold text-foreground">
                {BRANDING.name}
              </h1>
            </div>

            {/* Search Bar - Center */}
            <div className="flex-1 max-w-2xl mx-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="text"
                  placeholder={BRANDING.ui.searchPlaceholder}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-input rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                />
              </div>
            </div>

            {/* Theme Toggle - Right */}
            <div className="shrink-0">
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
