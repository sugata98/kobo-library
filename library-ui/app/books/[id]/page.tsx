"use client";

import { useState, useEffect, use } from "react";
import {
  getBookHighlights,
  getBookMarkups,
  getBookDetails,
  getBookCoverUrl,
} from "@/lib/api";
import Link from "next/link";

// Use the backend proxy endpoints
const getSvgUrl = (markupId: string) =>
  `${
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
  }/markup/${markupId}/svg`;

const getJpgUrl = (markupId: string) =>
  `${
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
  }/markup/${markupId}/jpg`;

/**
 * Displays a book cover image when available and a persistent placeholder otherwise.
 *
 * Fetches a cover URL for the given title (and optional author or ISBN) and renders the image; if fetching or image loading fails, a stylized placeholder is shown.
 *
 * @param title - The book title used to request a cover image
 * @param author - Optional author name to improve cover lookup
 * @param isbn - Optional ISBN to improve cover lookup
 * @returns A JSX element containing either the fetched cover image or a placeholder graphic
 */
function BookCoverImage({
  title,
  author,
  isbn,
}: {
  title: string;
  author?: string;
  isbn?: string;
}) {
  const [coverUrl, setCoverUrl] = useState<string | null>(null);

  useEffect(() => {
    if (title) {
      getBookCoverUrl(title, author, isbn)
        .then((url) => {
          setCoverUrl(url);
        })
        .catch(() => {
          // Silently fail, placeholder will show
        });
    }
  }, [title, author, isbn]);

  return (
    <div className="relative w-32 h-48 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 overflow-hidden rounded-lg shadow-md">
      {coverUrl && (
        <img
          src={coverUrl}
          alt={`${title} cover`}
          className="w-full h-full object-cover"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.style.display = "none";
            const placeholder = target.parentElement?.querySelector(
              ".cover-placeholder"
            ) as HTMLElement;
            if (placeholder) {
              placeholder.style.display = "flex";
            }
          }}
        />
      )}
      <div className="cover-placeholder absolute inset-0 flex items-center justify-center text-gray-400 dark:text-gray-500">
        <svg
          className="w-12 h-12"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
          />
        </svg>
      </div>
    </div>
  );
}

/**
 * Render a detailed book page including cover, metadata, highlights, and markups.
 *
 * Displays a loading indicator while fetching book data and an error message if fetching fails.
 *
 * @param params - A promise that resolves to route parameters; the object must contain an encoded `id` for the book.
 * @returns The React element for the book details page (cover, title/author/progress, highlights list, and markups with image overlays).
 */
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
          <BookCoverImage
            title={bookInfo.Title}
            author={bookInfo.Author}
            isbn={bookInfo.ISBN}
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
                  <div className="border border-gray-200 p-2 rounded bg-white dark:bg-gray-900 relative inline-block">
                    {/* Container for overlay */}
                    <div className="relative">
                      {/* JPG Background */}
                      <img
                        src={getJpgUrl(m.BookmarkID)}
                        alt="Page"
                        className="max-w-full h-auto block"
                        onError={(e) => {
                          // If JPG fails, show fallback
                          const container = (e.target as HTMLImageElement)
                            .parentElement;
                          if (container) {
                            const fallback = container.querySelector(
                              ".fallback-message"
                            ) as HTMLElement;
                            if (fallback) fallback.classList.remove("hidden");
                          }
                        }}
                      />
                      {/* SVG Overlay (positioned absolutely on top) */}
                      <img
                        src={getSvgUrl(m.BookmarkID)}
                        alt="Markup"
                        className="absolute top-0 left-0 w-full h-full pointer-events-none"
                        style={{ mixBlendMode: "normal", opacity: 1 }}
                        onError={(e) => {
                          // If SVG fails, just hide it
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    </div>
                    {/* Fallback message */}
                    <div className="hidden fallback-message text-xs text-gray-400 text-center p-4">
                      Images not found in B2.
                      <br />
                      (ID: {m.BookmarkID})
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}