/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect, use } from "react";
import { getBookHighlights, getBookMarkups, getBookDetails } from "@/lib/api";
import Link from "next/link";
import BookCover from "@/components/BookCover";
import LocationIndicator from "@/components/LocationIndicator";

// Use the backend proxy endpoints
const getSvgUrl = (markupId: string) =>
  `${
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
  }/markup/${markupId}/svg`;

const getJpgUrl = (markupId: string) =>
  `${
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
  }/markup/${markupId}/jpg`;

// Component to handle markup image loading with state management and progressive loading
// Using <img> instead of Next.js Image for dynamic API endpoints with overlay behavior
/* eslint-disable @next/next/no-img-element */
function MarkupImage({ markupId }: { markupId: string }) {
  const [jpgLoaded, setJpgLoaded] = useState(false);
  const [svgLoaded, setSvgLoaded] = useState(false);
  const [jpgError, setJpgError] = useState(false);
  const [svgError, setSvgError] = useState(false);
  const [showFallback, setShowFallback] = useState(false);

  const handleJpgLoad = () => {
    setJpgLoaded(true);
  };

  const handleJpgError = () => {
    setJpgError(true);
    setShowFallback(true);
  };

  const handleSvgLoad = () => {
    setSvgLoaded(true);
  };

  const handleSvgError = () => {
    setSvgError(true);
  };

  return (
    <div className="border border-gray-200 p-2 rounded bg-white dark:bg-gray-900 relative w-full">
      {!showFallback && (
        <div className="relative min-h-[200px]">
          {/* Loader - stays in background, gets covered by JPG when it streams in */}
          {!jpgLoaded && !jpgError && (
            <div className="absolute inset-0 w-full min-h-[200px] bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 animate-pulse rounded flex items-center justify-center z-0">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 dark:border-gray-600 border-t-blue-500 dark:border-t-blue-400"></div>
            </div>
          )}

          {/* JPG Background - progressively loads and covers the loader as it streams */}
          <img
            src={getJpgUrl(markupId)}
            alt="Page"
            className="max-w-full h-auto block relative z-20"
            onLoad={handleJpgLoad}
            onError={handleJpgError}
            loading="eager"
            decoding="async"
          />

          {/* SVG Overlay (positioned absolutely on top) - waits for JPG to load */}
          {jpgLoaded && !svgError && (
            <img
              src={getSvgUrl(markupId)}
              alt="Markup"
              className="absolute top-0 left-0 w-full h-full pointer-events-none transition-opacity duration-300 z-30"
              style={{ mixBlendMode: "normal", opacity: svgLoaded ? 1 : 0 }}
              onLoad={handleSvgLoad}
              onError={handleSvgError}
            />
          )}
        </div>
      )}

      {/* Fallback message */}
      {showFallback && (
        <div className="text-xs text-gray-400 text-center p-4">
          Images not found in B2.
          <br />
          (ID: {markupId})
        </div>
      )}
    </div>
  );
}

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

  if (loading) return <div className="p-8">Loading details...</div>;
  if (error) return <div className="p-8 text-red-500">Error: {error}</div>;

  return (
    <div className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Link
        href="/"
        className="text-blue-500 hover:underline mb-4 inline-block"
      >
        &larr; Back to Library
      </Link>

      <div className="flex items-start gap-6 mb-6">
        {bookInfo && (
          <BookCover
            title={bookInfo.Title}
            author={bookInfo.Author}
            isbn={bookInfo.ISBN}
            imageUrl={bookInfo.ImageUrl}
            className="relative w-32 h-48 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 overflow-hidden rounded-lg shadow-md"
            iconSize="w-12 h-12"
          />
        )}
        <div>
          <h1 className="text-2xl font-bold mb-2">
            {bookInfo?.Title || `Book ID: ${decodeURIComponent(id)}`}
          </h1>
          {bookInfo?.Author && (
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
              by {bookInfo.Author}
            </p>
          )}
          {bookInfo && (
            <div className="space-y-1">
              {bookInfo.ISBN && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  ISBN: {bookInfo.ISBN}
                </p>
              )}
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Progress: {Math.round(bookInfo.___PercentRead || 0)}%
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section>
          <h2 className="text-xl font-semibold mb-4 border-b pb-2">
            Highlights ({highlights.length})
          </h2>
          <div className="space-y-6">
            {highlights.length === 0 ? (
              <p className="text-gray-500">No highlights found.</p>
            ) : (
              (() => {
                const groupedHighlights = groupByChapter(highlights);
                return Object.entries(groupedHighlights).map(
                  ([chapter, items]) => (
                    <div key={chapter} className="space-y-3">
                      {/* Chapter header */}
                      <div className="sticky top-0 bg-gray-50 dark:bg-gray-900 py-2 z-50">
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                          {chapter}
                        </h3>
                        <div className="h-px bg-gradient-to-r from-blue-500 to-transparent mt-1"></div>
                      </div>

                      {/* Chapter items */}
                      {items.map((h: any, idx: number) => (
                        <div
                          key={h.BookmarkID}
                          className="bg-white dark:bg-gray-800 p-4 rounded shadow"
                        >
                          <blockquote className="border-l-4 border-yellow-400 pl-4 italic mb-3">
                            &ldquo;{h.Text}&rdquo;
                          </blockquote>

                          <LocationIndicator
                            index={idx + 1}
                            total={items.length}
                            chapterName={null}
                            chapterProgress={h.TrueChapterProgress}
                            className="mb-2"
                          />

                          <div className="text-xs text-gray-400 mt-2 text-right">
                            {new Date(h.DateCreated).toLocaleDateString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                );
              })()
            )}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4 border-b pb-2">
            Markups ({markups.length})
          </h2>
          <div className="space-y-6">
            {markups.length === 0 ? (
              <p className="text-gray-500">No markups found.</p>
            ) : (
              (() => {
                const groupedMarkups = groupByChapter(markups);
                return Object.entries(groupedMarkups).map(
                  ([chapter, items]) => (
                    <div key={chapter} className="space-y-3">
                      {/* Chapter header */}
                      <div className="sticky top-0 bg-gray-50 dark:bg-gray-900 py-2 z-50">
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                          {chapter}
                        </h3>
                        <div className="h-px bg-gradient-to-r from-purple-500 to-transparent mt-1"></div>
                      </div>

                      {/* Chapter items */}
                      {items.map((m: any, idx: number) => (
                        <div
                          key={m.BookmarkID}
                          className="bg-white dark:bg-gray-800 p-4 rounded shadow"
                        >
                          <LocationIndicator
                            index={idx + 1}
                            total={items.length}
                            chapterName={null}
                            chapterProgress={m.TrueChapterProgress}
                            className="mb-3"
                          />

                          <MarkupImage markupId={m.BookmarkID} />

                          <div className="text-xs text-gray-400 mt-2 text-right">
                            {new Date(m.DateCreated).toLocaleDateString()}
                          </div>
                        </div>
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
