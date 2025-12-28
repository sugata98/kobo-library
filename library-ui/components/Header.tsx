"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import Image from "next/image";
import { ModeToggle } from "@/components/ThemeToggle";
import { LogoutButton } from "@/components/LogoutButton";
import { SyncStatusBadge } from "@/components/SyncStatusBadge";
import { BRANDING } from "@/lib/branding";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface CheckAndSyncResponse {
  sync_needed: boolean;
  sync_status: "up_to_date" | "completed" | "error";
  message: string;
}

export function Header() {
  const pathname = usePathname();
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAndSync();
  }, []);

  async function checkAndSync() {
    try {
      setIsSyncing(true);

      const response = await fetch(`${API_BASE_URL}/check-and-sync`, {
        method: "POST",
        credentials: "include",
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          setIsSyncing(false);
          return;
        }
        throw new Error(`Sync failed: ${response.statusText}`);
      }

      const data: CheckAndSyncResponse = await response.json();

      if (data.sync_status === "completed") {
        // Database was updated - reload page to show fresh data
        window.location.reload();
      } else if (data.sync_status === "up_to_date") {
        // No sync needed - hide badge
        setIsSyncing(false);
        setError(null);
      } else if (data.sync_status === "error") {
        // Error - show error badge
        setIsSyncing(false);
        setError(data.message);
      }
    } catch (error) {
      console.error("Sync error:", error);
      setIsSyncing(false);
      setError(error instanceof Error ? error.message : "Unknown error");
    }
  }

  // Don't show header on login or offline pages
  if (pathname === "/login" || pathname === "/offline") {
    return null;
  }

  return (
    <header className="bg-card border-b border-border shadow-sm sticky top-0 z-50">
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
              <h1 className="text-xl md:text-2xl font-bold bg-linear-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent tracking-tight leading-tight">
                {BRANDING.name}
              </h1>
              <p className="text-[10px] md:text-xs text-muted-foreground leading-tight">
                {BRANDING.tagline}
              </p>
            </div>
          </div>

          {/* Sync Status, Theme Toggle and Logout */}
          <div className="shrink-0 flex items-center gap-3">
            <SyncStatusBadge isSyncing={isSyncing} error={error} />
            <ModeToggle />
            <LogoutButton />
          </div>
        </div>
      </div>
    </header>
  );
}
