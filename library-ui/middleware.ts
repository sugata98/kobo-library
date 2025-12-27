import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Configuration
const AUTH_TIMEOUT_MS = 3000; // 3 seconds timeout for auth verification
const CACHE_TTL_MS = 30000; // 30 seconds cache for auth results
const ALLOW_ON_NETWORK_ERROR = false; // Set to true to allow access on network errors (less secure but better UX)

// Simple in-memory cache for auth verification results
interface CacheEntry {
  authenticated: boolean;
  timestamp: number;
}

const authCache = new Map<string, CacheEntry>();

/**
 * Fetch with timeout wrapper
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

/**
 * Check if cached auth result is still valid
 */
function getCachedAuth(cacheKey: string): boolean | null {
  const cached = authCache.get(cacheKey);

  if (!cached) {
    return null;
  }

  const age = Date.now() - cached.timestamp;

  if (age > CACHE_TTL_MS) {
    // Cache expired, remove it
    authCache.delete(cacheKey);
    return null;
  }

  return cached.authenticated;
}

/**
 * Cache auth verification result
 */
function setCachedAuth(cacheKey: string, authenticated: boolean): void {
  authCache.set(cacheKey, {
    authenticated,
    timestamp: Date.now(),
  });

  // Simple cache cleanup: remove entries older than TTL
  // This runs periodically to prevent memory leaks
  if (authCache.size > 1000) {
    const now = Date.now();
    for (const [key, entry] of authCache.entries()) {
      if (now - entry.timestamp > CACHE_TTL_MS) {
        authCache.delete(key);
      }
    }
  }
}

export async function middleware(request: NextRequest) {
  // Skip middleware for login page and static assets
  if (
    request.nextUrl.pathname === "/login" ||
    request.nextUrl.pathname.startsWith("/_next") ||
    request.nextUrl.pathname.startsWith("/api") ||
    request.nextUrl.pathname.match(
      /\.(ico|png|jpg|jpeg|svg|gif|webp|woff|woff2|ttf|eot)$/
    )
  ) {
    return NextResponse.next();
  }

  const cookie = request.cookies.get("access_token");

  // No cookie = not authenticated
  if (!cookie) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Check cache first
  const cacheKey = `auth:${cookie.value}`;
  const cachedResult = getCachedAuth(cacheKey);

  if (cachedResult !== null) {
    // Cache hit
    if (cachedResult) {
      return NextResponse.next();
    } else {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }

  // Cache miss - verify with backend
  try {
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/auth/verify`,
      {
        headers: {
          Cookie: `access_token=${cookie.value}`,
        },
        cache: "no-store",
      },
      AUTH_TIMEOUT_MS
    );

    if (!response.ok) {
      // Authentication failed (401, 403, etc.)
      console.warn(
        `Auth verification failed: ${response.status} ${response.statusText}`
      );
      setCachedAuth(cacheKey, false);
      return NextResponse.redirect(new URL("/login", request.url));
    }

    const data = await response.json();

    if (!data.authenticated) {
      // Not authenticated
      setCachedAuth(cacheKey, false);
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // Authenticated - cache the result
    setCachedAuth(cacheKey, true);
    return NextResponse.next();
  } catch (error) {
    // Distinguish between timeout/network errors and other errors
    const isNetworkError =
      error instanceof Error &&
      (error.name === "AbortError" ||
        error.message.includes("fetch") ||
        error.message.includes("network"));

    if (isNetworkError) {
      console.error(
        "Auth verification network error (backend unreachable or timeout):",
        error
      );

      if (ALLOW_ON_NETWORK_ERROR) {
        // Allow access but don't cache (less secure, better UX)
        console.warn(
          "⚠️  Allowing access despite network error (ALLOW_ON_NETWORK_ERROR=true)"
        );
        return NextResponse.next();
      } else {
        // Redirect to login for security (default behavior)
        console.warn(
          "Redirecting to login due to network error (ALLOW_ON_NETWORK_ERROR=false)"
        );
        return NextResponse.redirect(new URL("/login", request.url));
      }
    } else {
      // Other errors (parsing, etc.) - redirect to login
      console.error("Auth verification error:", error);
      return NextResponse.redirect(new URL("/login", request.url));
    }
  }
}

// Configure which routes to protect
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - /login (login page)
     * - /_next (Next.js internals)
     * - /api (API routes)
     * - Static files (images, fonts, etc.)
     */
    "/((?!login|_next|api|.*\\..*).*)",
  ],
};
