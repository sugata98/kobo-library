"use client";

import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";
import { logout } from "@/lib/auth";

export function LogoutButton() {
  const router = useRouter();
  const pathname = usePathname();

  // Don't show logout button on login page
  if (pathname === "/login") {
    return null;
  }

  const handleLogout = async () => {
    await logout();
    router.push("/login");
    router.refresh();
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleLogout}
      title="Logout"
      aria-label="Logout"
    >
      <LogOut className="h-5 w-5" />
    </Button>
  );
}

