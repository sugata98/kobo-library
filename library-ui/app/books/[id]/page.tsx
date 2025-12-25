"use client";

import { useState, useEffect, use } from "react";
import { getBookHighlights, getBookMarkups, getBookDetails } from "@/lib/api";
import Link from "next/link";
import BookCover from "@/components/BookCover";

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
function MarkupImage({ markupId }: { markupId: string }) {
  const [jpgLoaded, setJpgLoaded] = useState(false);
  const [svgLoaded, setSvgLoaded] = useState(false);
  const [jpgError, setJpgError] = useState(false);
  const [svgError, setSvgError] = useState(false);
  const [showFallback, setShowFallback] = useState(false);
  const [imageStartedLoading, setImageStartedLoading] = useState(false);

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

  // Show loader only before image starts loading
  // Once image starts, browser will progressively render it
  const showLoader = !imageStartedLoading && !jpgLoaded && !jpgError;

  return (
    <div className="border border-gray-200 p-2 rounded bg-white dark:bg-gray-900 relative w-full">
      {/* Container for overlay */}
      <div className="relative w-full min-h-[200px]">
        {/* Subtle skeleton loader - only shown before image starts loading */}
        {showLoader && (
          <div className="absolute inset-0 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 animate-pulse rounded flex items-center justify-center z-0">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 dark:border-gray-600 border-t-blue-500 dark:border-t-blue-400"></div>
          </div>
        )}

        {/* JPG Background - progressively loads as chunks arrive from streaming */}
        {!showFallback && (
          <img
            src={getJpgUrl(markupId)}
            alt="Page"
            className="w-full h-auto block relative z-10"
            onLoad={handleJpgLoad}
            onError={handleJpgError}
            onLoadStart={() => {
              setImageStartedLoading(true);
            }}
            onProgress={() => {
              // Hide loader as soon as we start receiving data
              setImageStartedLoading(true);
            }}
            loading="eager"
            decoding="async"
          />
        )}

        {/* SVG Overlay (positioned absolutely on top) */}
        {!svgError && jpgLoaded && (
          <img
            src={getSvgUrl(markupId)}
            alt="Markup"
            className="absolute top-0 left-0 w-full h-full pointer-events-none transition-opacity duration-300"
            style={{ mixBlendMode: "normal", opacity: svgLoaded ? 1 : 0 }}
            onLoad={handleSvgLoad}
            onError={handleSvgError}
          />
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
        // Sort markups by ordering number if available, then by date
        const sorted = m.sort((a: any, b: any) => {
          if (a.OrderingNumber && b.OrderingNumber) {
            return a.OrderingNumber.localeCompare(b.OrderingNumber);
          }
          return (
            new Date(a.DateCreated).getTime() -
            new Date(b.DateCreated).getTime()
          );
        });
        setMarkups(sorted);
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
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Progress: {Math.round(bookInfo.___PercentRead || 0)}%
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section>
          <h2 className="text-xl font-semibold mb-4 border-b pb-2">
            Highlights ({highlights.length})
          </h2>
          <div className="space-y-4">
            {highlights.length === 0 ? (
              <p className="text-gray-500">No highlights found.</p>
            ) : (
              highlights.map((h) => (
                <div
                  key={h.BookmarkID}
                  className="bg-white dark:bg-gray-800 p-4 rounded shadow"
                >
                  <blockquote className="border-l-4 border-yellow-400 pl-4 italic mb-2">
                    &ldquo;{h.Text}&rdquo;
                  </blockquote>
                  <div className="text-xs text-gray-400 mt-2 text-right">
                    {new Date(h.DateCreated).toLocaleDateString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4 border-b pb-2">
            Markups ({markups.length})
          </h2>
          <div className="space-y-4">
            {markups.length === 0 ? (
              <p className="text-gray-500">No markups found.</p>
            ) : (
              markups.map((m) => (
                <div
                  key={m.BookmarkID}
                  className="bg-white dark:bg-gray-800 p-4 rounded shadow"
                >
                  <div className="mb-2">
                    <span className="font-semibold text-sm">Markup ID:</span>{" "}
                    <span className="text-xs text-gray-500">
                      {m.BookmarkID}
                    </span>
                  </div>

                  {/* Metadata */}
                  {(m.SectionTitle || m.OrderingNumber || m.BookPartNumber) && (
                    <div className="text-xs text-gray-500 mb-2">
                      {m.SectionTitle && (
                        <span>Section: {m.SectionTitle} | </span>
                      )}
                      {m.BookPartNumber && (
                        <span>Part: {m.BookPartNumber} | </span>
                      )}
                      {m.OrderingNumber && (
                        <span>Order: {m.OrderingNumber}</span>
                      )}
                    </div>
                  )}

                  {/* Composite: JPG background with SVG overlay */}
                  <MarkupImage markupId={m.BookmarkID} />
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
