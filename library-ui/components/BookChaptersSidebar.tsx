"use client";

import { useState } from "react";
import { BookOpen, ChevronRight, X, List } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface SidebarChapter {
  name: string;
  /** DOM id of the scroll target element */
  id: string;
  highlightCount: number;
  markupCount: number;
}

interface BookChaptersSidebarProps {
  chapters: SidebarChapter[];
  activeChapterId?: string;
}

function ChapterList({
  chapters,
  activeChapterId,
  onSelect,
}: {
  chapters: SidebarChapter[];
  activeChapterId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <nav className="flex-1 overflow-y-auto py-2 px-1">
      {chapters.map((chapter) => {
        const isActive = activeChapterId === chapter.id;
        return (
          <button
            key={chapter.id}
            onClick={() => onSelect(chapter.id)}
            className={cn(
              "w-full flex items-start gap-2 px-3 py-2 text-left text-xs rounded-sm transition-colors",
              "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              isActive
                ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                : "text-sidebar-foreground"
            )}
          >
            <ChevronRight
              className={cn(
                "h-3 w-3 mt-0.5 shrink-0 transition-transform",
                isActive
                  ? "text-sidebar-primary-foreground"
                  : "text-sidebar-foreground/40"
              )}
            />
            <span className="flex-1 leading-snug">{chapter.name}</span>
            <div className="shrink-0 flex flex-col items-end gap-0.5 mt-0.5">
              {chapter.highlightCount > 0 && (
                <span
                  className={cn(
                    "text-[10px] tabular-nums",
                    isActive
                      ? "text-sidebar-primary-foreground/70"
                      : "text-sidebar-foreground/50"
                  )}
                >
                  {chapter.highlightCount}h
                </span>
              )}
              {chapter.markupCount > 0 && (
                <span
                  className={cn(
                    "text-[10px] tabular-nums",
                    isActive
                      ? "text-sidebar-primary-foreground/70"
                      : "text-sidebar-foreground/50"
                  )}
                >
                  {chapter.markupCount}m
                </span>
              )}
            </div>
          </button>
        );
      })}
    </nav>
  );
}

export function BookChaptersSidebar({
  chapters,
  activeChapterId,
}: BookChaptersSidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const scrollToChapter = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      const headerHeight =
        parseInt(
          getComputedStyle(document.documentElement)
            .getPropertyValue("--header-height")
            .trim()
        ) || 72;
      const top =
        el.getBoundingClientRect().top + window.scrollY - headerHeight - 8;
      window.scrollTo({ top, behavior: "smooth" });
    }
    setMobileOpen(false);
  };

  return (
    <>
      {/* Desktop sidebar — sticky left column */}
      <aside className="hidden lg:flex flex-col w-56 xl:w-64 shrink-0 sticky top-[var(--header-height)] h-[calc(100vh-var(--header-height))] bg-sidebar border-r border-sidebar-border overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-sidebar-border shrink-0">
          <BookOpen className="h-4 w-4 text-sidebar-primary shrink-0" />
          <span className="text-sm font-semibold text-sidebar-foreground">
            Chapters
          </span>
          <Badge variant="outline" className="ml-auto text-xs tabular-nums">
            {chapters.length}
          </Badge>
        </div>
        <ChapterList
          chapters={chapters}
          activeChapterId={activeChapterId}
          onSelect={scrollToChapter}
        />
      </aside>

      {/* Mobile: floating button */}
      <Button
        variant="outline"
        size="sm"
        className="fixed bottom-6 right-4 z-50 lg:hidden shadow-lg gap-1.5 rounded-full px-3"
        onClick={() => setMobileOpen(true)}
      >
        <List className="h-3.5 w-3.5" />
        <span className="text-xs font-medium">Chapters</span>
      </Button>

      {/* Mobile: overlay + drawer */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="fixed left-0 top-0 bottom-0 z-50 w-72 bg-sidebar border-r border-sidebar-border lg:hidden flex flex-col shadow-xl">
            <div className="flex items-center justify-between px-4 py-3 border-b border-sidebar-border shrink-0">
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-sidebar-primary" />
                <span className="text-sm font-semibold text-sidebar-foreground">
                  Chapters
                </span>
              </div>
              <button
                onClick={() => setMobileOpen(false)}
                className="h-7 w-7 flex items-center justify-center rounded-md hover:bg-sidebar-accent text-sidebar-foreground transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <ChapterList
              chapters={chapters}
              activeChapterId={activeChapterId}
              onSelect={scrollToChapter}
            />
          </aside>
        </>
      )}
    </>
  );
}
