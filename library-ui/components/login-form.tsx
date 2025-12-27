"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Eye, EyeOff } from "lucide-react";
import { BRANDING } from "@/lib/branding";
import Image from "next/image";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // Important: include cookies
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Login failed");
      }

      // Login successful, redirect to home
      // Next.js App Router automatically refreshes on navigation
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full shadow-2xl border-0 rounded-3xl backdrop-blur-sm bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-100 via-white to-gray-50 dark:from-gray-800 dark:via-gray-950 dark:to-gray-900 relative overflow-hidden">
      {/* Subtle grid pattern ON THE CARD */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>
      
      <CardContent className="pt-10 pb-8 px-10 relative z-10">
        {/* Logo and Title */}
        <div className="flex flex-col items-center space-y-2 mb-8">
          <div className="relative">
            <Image
              src="/logo.svg"
              alt={BRANDING.name}
              width={48}
              height={48}
              className="rounded-lg"
            />
            {/* Subtle glow effect */}
            <div className="absolute inset-0 -z-10 bg-primary/20 blur-xl rounded-lg"></div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Welcome Back</h1>
          <p className="text-sm text-muted-foreground text-center">
            Please enter your details to sign in
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username Field */}
          <div className="space-y-2">
            <Label htmlFor="username" className="text-sm font-medium">
              Username<span className="text-destructive">*</span>
            </Label>
            <Input
              id="username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              disabled={loading}
              className="h-12 rounded-xl border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Password Field with Toggle */}
          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium">
              Password<span className="text-destructive">*</span>
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={loading}
                className="h-12 pr-10 rounded-xl border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-primary/20"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3">
              <p className="text-sm text-destructive font-medium">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full h-12 text-base font-medium rounded-xl shadow-md hover:shadow-lg transition-all" 
            disabled={loading}
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Signing in...
              </>
            ) : (
              `Sign in to ${BRANDING.name}`
            )}
          </Button>
        </form>

        {/* Footer Text */}
        <div className="mt-6 text-center text-sm text-muted-foreground">
          Your personal reading companion
        </div>
      </CardContent>
    </Card>
  );
}

