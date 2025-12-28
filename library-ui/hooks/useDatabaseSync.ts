import { useState, useRef, useEffect } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const POLL_INTERVAL_MS = 1000; // Poll every 1 second
const MAX_POLL_ATTEMPTS = 120; // Max 2 minutes of polling
const FETCH_TIMEOUT_MS = 30000; // 30 second timeout for fetch requests

interface InitiateSyncResponse {
  initiated: boolean;
  message: string;
  status?: string;
  error?: string;
}

interface SyncStatusResponse {
  status:
    | "idle"
    | "checking"
    | "downloading"
    | "completed"
    | "up_to_date"
    | "error";
  message: string;
  progress?: number | null;
  error?: string | null;
  is_syncing: boolean;
  needs_reload: boolean;
  file_size_mb?: number | null;
}

interface UseDatabaseSyncOptions {
  autoSync?: boolean; // Whether to auto-sync on mount (default: true)
}

/**
 * Custom hook for managing database sync with the backend.
 * Handles:
 * - Initial sync check on mount
 * - Polling for sync status
 * - Timeout and abort handling
 * - Cleanup on unmount
 * - React 19 Strict Mode deduplication
 */
export function useDatabaseSync(options: UseDatabaseSyncOptions = {}) {
  const { autoSync = true } = options;

  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollAttemptsRef = useRef(0);
  const isSyncingRef = useRef(false); // Deduplication guard for React 19 Strict Mode
  const abortControllerRef = useRef<AbortController | null>(null); // For fetch cleanup

  useEffect(() => {
    if (!autoSync) return;

    // Prevent duplicate sync requests in React 19 Strict Mode (double useEffect calls)
    if (isSyncingRef.current) {
      console.log("Sync already in progress, skipping duplicate request");
      return;
    }

    isSyncingRef.current = true;
    initiateSync();

    // Cleanup polling and abort pending requests on unmount
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      isSyncingRef.current = false;
    };
  }, [autoSync]);

  async function initiateSync() {
    // Create new AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Set up timeout
    const timeoutId = setTimeout(() => {
      abortController.abort();
    }, FETCH_TIMEOUT_MS);

    try {
      setIsSyncing(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/check-and-sync`, {
        method: "POST",
        credentials: "include",
        signal: abortController.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          // Not authenticated, silently hide sync badge
          setIsSyncing(false);
          return;
        }
        throw new Error(`Failed to initiate sync: ${response.statusText}`);
      }

      const data: InitiateSyncResponse = await response.json();

      if (data.initiated) {
        // Sync was initiated, start polling for status
        console.log("Sync initiated, starting status polling...");
        startPolling();
      } else {
        // Sync not needed or already in progress
        console.log(data.message);

        // Check current state
        if (data.status === "up_to_date") {
          setIsSyncing(false);
        } else if (data.status === "error") {
          setIsSyncing(false);
          setError(data.error || "Sync error");
        } else if (
          data.status === "checking" ||
          data.status === "downloading"
        ) {
          // Already syncing, start polling
          startPolling();
        } else {
          setIsSyncing(false);
        }
      }
    } catch (err) {
      clearTimeout(timeoutId);

      // Handle abort errors gracefully (component unmounted or timeout)
      if (err instanceof Error && err.name === "AbortError") {
        console.log("Sync request aborted (timeout or unmount)");
        setIsSyncing(false);
        return;
      }

      console.error("Sync initiation error:", err);
      setIsSyncing(false);
      setError(err instanceof Error ? err.message : "Failed to initiate sync");
    } finally {
      // Clear the abort controller reference
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
    }
  }

  function startPolling() {
    // Clear any existing polling
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    pollAttemptsRef.current = 0;

    // Poll immediately first
    pollStatus();

    // Then set up interval
    pollIntervalRef.current = setInterval(() => {
      pollStatus();
    }, POLL_INTERVAL_MS);
  }

  function stopPolling() {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    pollAttemptsRef.current = 0;
  }

  async function pollStatus() {
    // Create new AbortController for this poll request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Set up timeout
    const timeoutId = setTimeout(() => {
      abortController.abort();
    }, FETCH_TIMEOUT_MS);

    try {
      pollAttemptsRef.current += 1;

      // Check max attempts
      if (pollAttemptsRef.current > MAX_POLL_ATTEMPTS) {
        console.warn("Max polling attempts reached, stopping...");
        stopPolling();
        setIsSyncing(false);
        setError("Sync timeout - please refresh the page");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/sync-status`, {
        method: "GET",
        credentials: "include",
        signal: abortController.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          stopPolling();
          setIsSyncing(false);
          return;
        }
        throw new Error(`Failed to get sync status: ${response.statusText}`);
      }

      const data: SyncStatusResponse = await response.json();

      console.log(
        `Sync status: ${data.status} (attempt ${pollAttemptsRef.current})`
      );

      // Update UI based on status
      if (data.status === "completed") {
        // Sync completed, reload page to show fresh data
        console.log("Sync completed, reloading page...");
        stopPolling();
        // Small delay before reload to ensure state is updated
        setTimeout(() => {
          window.location.reload();
        }, 500);
      } else if (data.status === "up_to_date") {
        // Already up to date, stop polling
        console.log("Database is up to date");
        stopPolling();
        setIsSyncing(false);
        setError(null);
      } else if (data.status === "error") {
        // Error occurred
        console.error("Sync error:", data.error);
        stopPolling();
        setIsSyncing(false);
        setError(data.error || "Sync failed");
      } else if (data.status === "checking" || data.status === "downloading") {
        // Still syncing, keep polling
        setIsSyncing(true);
        setError(null);
      } else {
        // Idle or unknown status
        stopPolling();
        setIsSyncing(false);
      }
    } catch (err) {
      clearTimeout(timeoutId);

      // Handle abort errors gracefully (component unmounted or timeout)
      if (err instanceof Error && err.name === "AbortError") {
        console.log("Poll request aborted (timeout or unmount)");
        stopPolling();
        setIsSyncing(false);
        return;
      }

      console.error("Status polling error:", err);
      stopPolling();
      setIsSyncing(false);
      setError(
        err instanceof Error ? err.message : "Failed to check sync status"
      );
    } finally {
      // Clear the abort controller reference
      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null;
      }
    }
  }

  // Return the hook's public API
  return {
    isSyncing,
    error,
    initiateSync, // Expose for manual triggering if needed
  };
}

