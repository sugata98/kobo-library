/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect } from "react";
import { getBooks } from "@/lib/api";
import Link from "next/link";
import BookCover from "./BookCover";
import { Card, CardContent } from "@/components/ui/card";

export default function BookList({
  searchQuery = "",
}: {
  searchQuery?: string;
}) {
  const [books, setBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 0,
  });
  const [allBooksForSearch, setAllBooksForSearch] = useState<any[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const pageSize = 10;

  // Fetch paginated books
  useEffect(() => {
    if (searchQuery) return; // Don't fetch paginated when searching

    let cancelled = false;

    (async () => {
      setLoading(true);
      try {
        const response = await getBooks(currentPage, pageSize);

        if (cancelled) return;

        // Response now has { books: [], pagination: {} }
        const allBooks = response.books || response;
        setBooks(allBooks);

        // Sync state from API response - make API the source of truth
        if (response.pagination) {
          setPagination(response.pagination);
          setCurrentPage(response.pagination.page);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [currentPage, searchQuery]);

  // When searching, use server-side search
  useEffect(() => {
    if (searchQuery) {
      setSearchLoading(true);
      getBooks(1, 100, searchQuery) // Use server-side search with max page size
        .then((response) => {
          const allBooks = response.books || response;
          // Ensure we always have an array, even if response structure is unexpected
          setAllBooksForSearch(Array.isArray(allBooks) ? allBooks : []);
        })
        .catch(() => {
          setAllBooksForSearch([]);
        })
        .finally(() => setSearchLoading(false));
    } else {
      setAllBooksForSearch([]);
    }
  }, [searchQuery]);

  if (loading && !searchQuery) return <div>Loading books...</div>;
  if (error) return <div className="text-destructive">Error: {error}</div>;

  // Use server-filtered results directly when searching, paginated results otherwise
  const displayBooks = searchQuery ? allBooksForSearch : books;

  const handlePageChange = (newPage: number) => {
    // Request the intended page but don't update state directly
    // State will be updated from the API response to keep it in sync
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <>
      {(loading || searchLoading) && (
        <div className="text-center py-8 text-muted-foreground">
          Loading books...
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {displayBooks.map((book) => (
          <Link
            href={`/books/${encodeURIComponent(book.ContentID)}`}
            key={book.ContentID}
          >
            <Card className="overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer group flex flex-col h-full">
              {/* Book Cover */}
              <BookCover
                title={book.Title}
                author={book.Author}
                isbn={book.ISBN}
                imageUrl={book.ImageUrl}
                className="relative w-full aspect-[2/3] bg-gradient-to-br from-muted to-muted/80 overflow-hidden"
                iconSize="w-16 h-16"
                showPlaceholderText={true}
                imageClassName="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />

              {/* Book Info */}
              <CardContent className="p-0 pt-4 px-4 pb-4 flex-1 flex flex-col">
                <h3 className="font-bold text-lg mb-1 line-clamp-2 group-hover:text-primary transition-colors min-h-[3.5rem]">
                  {book.Title}
                </h3>
                <p className="text-sm text-muted-foreground mb-3 line-clamp-1">
                  {book.Author || "Unknown Author"}
                </p>
                <div className="flex items-center justify-between mt-auto">
                  <div className="text-xs text-muted-foreground">
                    Progress: {Math.round(book.___PercentRead || 0)}%
                  </div>
                  {/* Progress bar */}
                  <div className="flex-1 ml-3 h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{
                        width: `${Math.round(book.___PercentRead || 0)}%`,
                      }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Pagination Controls - Only show when not searching */}
      {!searchQuery && !loading && pagination.total_pages > 1 && (
        <div className="mt-8 flex justify-center items-center gap-2">
          <button
            onClick={() => handlePageChange(pagination.page - 1)}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-input rounded-lg bg-background text-foreground hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>

          <span className="px-4 py-2 text-sm text-muted-foreground">
            Page {pagination.page} of {pagination.total_pages} (
            {pagination.total} books)
          </span>

          <button
            onClick={() => handlePageChange(pagination.page + 1)}
            disabled={pagination.page >= pagination.total_pages}
            className="px-4 py-2 border border-input rounded-lg bg-background text-foreground hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </>
  );
}
