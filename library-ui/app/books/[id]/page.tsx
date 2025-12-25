"use client";

import { useState, useEffect, use } from "react";
import { getBookHighlights, getBookMarkups } from "@/lib/api";
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

export default function BookDetails({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [markups, setMarkups] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const bookId = decodeURIComponent(id);

    Promise.all([getBookHighlights(bookId), getBookMarkups(bookId)])
      .then(([h, m]) => {
        setHighlights(h);
        // Sort markups by ordering number if available, then by date
        const sorted = m.sort((a, b) => {
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

      <h1 className="text-2xl font-bold mb-6 break-all">
        Book ID: {decodeURIComponent(id)}
      </h1>

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
                    "{h.Text}"
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
