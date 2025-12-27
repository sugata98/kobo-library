"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";
import { logout } from "@/lib/auth";

export function LogoutButton() {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  // Don't show logout button on login page
  if (pathname === "/login") {
    return null;
  }

  const handleLogout = async () => {
    if (isLoggingOut) return; // Prevent double-clicks

    setIsLoggingOut(true);

    try {
      const success = await logout();

      if (success) {
        // Logout successful, redirect to login page
        // Next.js App Router automatically refreshes on navigation
        router.push("/login");
      } else {
        // Logout failed, but still redirect to login page for security
        // (server-side middleware will handle auth validation)
        console.warn("Logout request failed, redirecting to login anyway");
        router.push("/login");
      }
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleLogout}
      title="Logout"
      aria-label="Logout"
      disabled={isLoggingOut}
    >
      <LogOut className={`h-5 w-5 ${isLoggingOut ? "animate-pulse" : ""}`} />
    </Button>
  );
}
