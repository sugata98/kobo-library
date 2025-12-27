import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function middleware(request: NextRequest) {
  // Skip middleware for login page and static assets
  if (
    request.nextUrl.pathname === "/login" ||
    request.nextUrl.pathname.startsWith("/_next") ||
    request.nextUrl.pathname.startsWith("/api") ||
    request.nextUrl.pathname.match(/\.(ico|png|jpg|jpeg|svg|gif|webp|woff|woff2|ttf|eot)$/)
  ) {
    return NextResponse.next();
  }

  // Check authentication by forwarding the cookie to the backend
  try {
    const cookie = request.cookies.get("access_token");
    
    const response = await fetch(`${API_BASE_URL}/auth/verify`, {
      headers: {
        Cookie: cookie ? `access_token=${cookie.value}` : "",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      // Not authenticated, redirect to login
      return NextResponse.redirect(new URL("/login", request.url));
    }

    const data = await response.json();
    
    if (!data.authenticated) {
      // Not authenticated, redirect to login
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // Authenticated, allow access
    return NextResponse.next();
  } catch (error) {
    console.error("Middleware auth check failed:", error);
    // On error, redirect to login for safety
    return NextResponse.redirect(new URL("/login", request.url));
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

