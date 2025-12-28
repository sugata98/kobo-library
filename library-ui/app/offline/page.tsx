import { BookOpen, WifiOff } from "lucide-react";
import Link from "next/link";

export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="relative">
            <BookOpen className="w-24 h-24 text-muted-foreground/50" />
            <div className="absolute -bottom-2 -right-2 bg-background rounded-full p-2 border-2">
              <WifiOff className="w-8 h-8 text-destructive" />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            You&apos;re Offline
          </h1>
          <p className="text-muted-foreground">
            It looks like you&apos;ve lost your internet connection. Some
            content may not be available.
          </p>
        </div>

        <div className="space-y-3 pt-4">
          <Link
            href="/"
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 w-full"
          >
            Return to Library
          </Link>
          <p className="text-sm text-muted-foreground">
            Previously viewed books and highlights are cached for offline access
          </p>
        </div>
      </div>
    </div>
  );
}
