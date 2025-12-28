"use client";

import { Loader2, AlertCircle } from "lucide-react";

interface SyncStatusBadgeProps {
  isSyncing: boolean;
  error: string | null;
}

export function SyncStatusBadge({ isSyncing, error }: SyncStatusBadgeProps) {
  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-500">
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm font-medium">Sync failed</span>
      </div>
    );
  }

  if (isSyncing) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm font-medium">Syncing</span>
      </div>
    );
  }

  return null;
}
