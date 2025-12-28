/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect, use } from "react";
import { getBookHighlights, getBookMarkups, getBookDetails } from "@/lib/api";
import Link from "next/link";
import BookCover from "@/components/BookCover";
import LocationIndicator from "@/components/LocationIndicator";
import LazyMarkupImage from "@/components/LazyMarkupImage";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Highlighter, ImageIcon, BookOpen } from "lucide-react";
import { BRANDING } from "@/lib/branding";

export default function BookDetails({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [markups, setMarkups] = useState<any[]>([]);
  const [bookInfo, setBookInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Helper function to group items by chapter
  const groupByChapter = (items: any[]) => {
    const sorted = items.sort((a: any, b: any) => {
      // Sort by OrderingNumber (if available), then date
      if (a.OrderingNumber && b.OrderingNumber) {
        return a.OrderingNumber.localeCompare(b.OrderingNumber, undefined, {
          numeric: true,
        });
      }
      return (
        new Date(a.DateCreated).getTime() - new Date(b.DateCreated).getTime()
      );
    });

    // Group by ChapterName
    const grouped: Record<string, any[]> = {};
    sorted.forEach((item) => {
      const chapter = item.ChapterName || "Unknown Chapter";
      if (!grouped[chapter]) {
        grouped[chapter] = [];
      }
      grouped[chapter].push(item);
    });

    return grouped;
  };

  useEffect(() => {
    const bookId = decodeURIComponent(id);

    Promise.all([
      getBookDetails(bookId),
      getBookHighlights(bookId),
      getBookMarkups(bookId),
    ])
      .then(([book, h, m]) => {
        setBookInfo(book);
        setHighlights(h);
        setMarkups(m);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (error)
    return <div className="p-4 md:p-8 text-destructive">Error: {error}</div>;

  if (loading) {
    return (
      <div className="min-h-screen p-4 md:p-8 bg-background text-foreground">
        <Skeleton className="h-6 w-32 mb-4" />

        <div className="flex items-start gap-6 mb-6">
          {/* Book cover skeleton */}
          <Skeleton className="w-48 aspect-2/3 rounded-lg" />

          {/* Book info skeleton */}
          <div className="flex-1 space-y-4">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-4 w-1/4" />
            <div className="space-y-2 mt-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Highlights section skeleton */}
          <div>
            <Skeleton className="h-8 w-48 mb-4" />
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="p-4 border border-border rounded-lg space-y-3"
                >
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <Skeleton className="h-3 w-32 mt-2" />
                </div>
              ))}
            </div>
          </div>

          {/* Markups section skeleton */}
          <div>
            <Skeleton className="h-8 w-48 mb-4" />
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-64 rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8 bg-background text-foreground">
      <Link
        href="/"
        className="inline-flex items-center gap-2 h-9 px-3 mb-4 -ml-2 rounded-md text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
      >
        {BRANDING.ui.backToLibrary}
      </Link>

      <div className="flex items-start gap-6 mb-6">
        {bookInfo && (
          <div className="relative">
            <BookCover
              title={bookInfo.Title}
              author={bookInfo.Author}
              isbn={bookInfo.ISBN}
              imageUrl={bookInfo.ImageUrl}
              className="relative w-32 h-48 bg-linear-to-br from-muted to-muted/80 overflow-hidden rounded-lg shadow-xl hover:shadow-2xl transition-shadow duration-300"
              iconSize="w-12 h-12"
            />
            {/* Gradient glow effect underneath */}
            <div className="absolute inset-0 -z-10 bg-linear-to-b from-primary/20 via-primary/10 to-transparent blur-xl translate-y-4 rounded-lg"></div>
          </div>
        )}
        <div>
          <h1 className="text-2xl font-bold mb-2">
            {bookInfo?.Title || `Book ID: ${decodeURIComponent(id)}`}
          </h1>
          {bookInfo?.Author && (
            <p className="text-lg text-muted-foreground mb-2">
              by {bookInfo.Author}
            </p>
          )}
          {bookInfo && (
            <div className="space-y-3">
              {bookInfo.ISBN && (
                <p className="text-sm text-muted-foreground">
                  ISBN: {bookInfo.ISBN}
                </p>
              )}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    Reading Progress
                  </span>
                  <span className="font-medium text-foreground">
                    {Math.round(bookInfo.___PercentRead || 0)}%
                  </span>
                </div>
                <Progress
                  value={Math.round(bookInfo.___PercentRead || 0)}
                  className="h-2"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section>
          {/* Highlights header badge */}
          <div className="mb-6">
            <Badge
              variant="secondary"
              className="w-full text-base font-semibold px-6 py-4 flex items-center justify-center gap-2"
            >
              <span>Highlights</span>
              <Badge variant="outline" className="text-xs font-medium">
                {highlights.length}
              </Badge>
            </Badge>
          </div>
          <div className="space-y-6">
            {highlights.length === 0 ? (
              <Empty className="border border-dashed">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <Highlighter />
                  </EmptyMedia>
                  <EmptyTitle>No Highlights Yet</EmptyTitle>
                  <EmptyDescription>
                    {BRANDING.ui.noHighlights}
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : (
              (() => {
                const groupedHighlights = groupByChapter(highlights);
                return Object.entries(groupedHighlights).map(
                  ([chapter, items]) => (
                    <div key={chapter} className="space-y-3">
                      {/* Chapter header */}
                      <div className="sticky top-0 bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80 py-3 px-4 -mx-4 z-50 border-b border-border/40 shadow-sm">
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-4 w-4 text-primary shrink-0" />
                          <h3 className="text-sm font-semibold text-foreground tracking-wide flex-1">
                            {chapter}
                          </h3>
                          <Badge variant="secondary" className="text-xs">
                            {items.length}
                          </Badge>
                        </div>
                      </div>

                      {/* Chapter items */}
                      {items.map((h: any, idx: number) => (
                        <Card
                          key={h.BookmarkID}
                          className="hover:shadow-lg transition-shadow overflow-hidden"
                        >
                          <div className="relative">
                            <CardContent className="pt-4 md:pt-6 pb-10 md:pb-12">
                              <blockquote className="border-l-4 border-primary pl-4 italic">
                                &ldquo;{h.Text}&rdquo;
                              </blockquote>
                            </CardContent>

                            {/* Bottom overlay with metadata */}
                            <div className="absolute bottom-0 left-0 right-0 z-10 pointer-events-auto">
                              <div className="py-2 md:py-2.5 bg-linear-to-t from-background via-background/60 via-30% to-transparent">
                                <div className="flex items-center justify-between gap-2 px-6">
                                  <LocationIndicator
                                    index={idx + 1}
                                    total={items.length}
                                    chapterName={null}
                                    chapterProgress={h.TrueChapterProgress}
                                    className="flex-1 min-w-0"
                                  />
                                  <div className="text-xs text-muted-foreground shrink-0 font-medium">
                                    {new Date(h.DateCreated).toLocaleDateString(
                                      "en-US",
                                      {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                      }
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  )
                );
              })()
            )}
          </div>
        </section>

        <section>
          {/* Markups header badge */}
          <div className="mb-6">
            <Badge
              variant="secondary"
              className="w-full text-base font-semibold px-6 py-4 flex items-center justify-center gap-2"
            >
              <span>Markups</span>
              <Badge variant="outline" className="text-xs font-medium">
                {markups.length}
              </Badge>
            </Badge>
          </div>

          <div className="space-y-6">
            {markups.length === 0 ? (
              <Empty className="border border-dashed">
                <EmptyHeader>
                  <EmptyMedia variant="icon">
                    <ImageIcon />
                  </EmptyMedia>
                  <EmptyTitle>No Markups Yet</EmptyTitle>
                  <EmptyDescription>{BRANDING.ui.noMarkups}</EmptyDescription>
                </EmptyHeader>
              </Empty>
            ) : (
              (() => {
                const groupedMarkups = groupByChapter(markups);
                return Object.entries(groupedMarkups).map(
                  ([chapter, items]) => (
                    <div key={chapter} className="space-y-3">
                      {/* Chapter header */}
                      <div className="sticky top-0 bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80 py-3 px-4 -mx-4 z-50 border-b border-border/40 shadow-sm">
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-4 w-4 text-primary shrink-0" />
                          <h3 className="text-sm font-semibold text-foreground tracking-wide flex-1">
                            {chapter}
                          </h3>
                          <Badge variant="secondary" className="text-xs">
                            {items.length}
                          </Badge>
                        </div>
                      </div>

                      {/* Chapter items - Priority load first 3, lazy load rest */}
                      {items.map((m: any, idx: number) => (
                        <Card
                          key={m.BookmarkID}
                          className="hover:shadow-lg transition-shadow overflow-hidden"
                        >
                          <LazyMarkupImage
                            markupId={m.BookmarkID}
                            priority={idx < 3}
                            preloadMargin="400px"
                            overlay={
                              <div className="pb-2 pt-4 md:pb-3 md:pt-8 bg-linear-to-t from-background via-background/60 via-30% to-transparent">
                                <div className="flex items-center justify-between gap-2 px-3">
                                  <LocationIndicator
                                    index={idx + 1}
                                    total={items.length}
                                    chapterName={null}
                                    chapterProgress={m.TrueChapterProgress}
                                    className="flex-1 min-w-0"
                                  />
                                  <div className="text-xs text-muted-foreground shrink-0 font-medium">
                                    {new Date(m.DateCreated).toLocaleDateString(
                                      "en-US",
                                      {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                      }
                                    )}
                                  </div>
                                </div>
                              </div>
                            }
                          />
                        </Card>
                      ))}
                    </div>
                  )
                );
              })()
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
