/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect } from "react";
import { getBooks } from "@/lib/api";
import Link from "next/link";
import BookCover from "./BookCover";

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
          setAllBooksForSearch(allBooks);
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
  if (error) return <div className="text-red-500">Error: {error}</div>;

  // Filter books based on search query
  const displayBooks = searchQuery
    ? allBooksForSearch.filter((book) => {
        const query = searchQuery.toLowerCase();
        const title = (book.Title || "").toLowerCase();
        const author = (book.Author || "").toLowerCase();
        return title.includes(query) || author.includes(query);
      })
    : books;

  const handlePageChange = (newPage: number) => {
    // Request the intended page but don't update state directly
    // State will be updated from the API response to keep it in sync
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <>
      {(loading || searchLoading) && (
        <div className="text-center py-8 text-gray-500">Loading books...</div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {displayBooks.map((book) => (
          <Link
            href={`/books/${encodeURIComponent(book.ContentID)}`}
            key={book.ContentID}
          >
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer bg-white dark:bg-gray-800 group">
              {/* Book Cover */}
              <BookCover
                title={book.Title}
                author={book.Author}
                isbn={book.ISBN}
                className="relative w-full aspect-[2/3] max-h-48 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 overflow-hidden"
                iconSize="w-16 h-16"
                showPlaceholderText={true}
                imageClassName="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />

              {/* Book Info */}
              <div className="p-4">
                <h3 className="font-bold text-lg mb-1 line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {book.Title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-1">
                  {book.Author || "Unknown Author"}
                </p>
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Progress: {Math.round(book.___PercentRead || 0)}%
                  </div>
                  {/* Progress bar */}
                  <div className="flex-1 ml-3 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 dark:bg-blue-400 transition-all duration-300"
                      style={{
                        width: `${Math.round(book.___PercentRead || 0)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Pagination Controls - Only show when not searching */}
      {!searchQuery && !loading && pagination.total_pages > 1 && (
        <div className="mt-8 flex justify-center items-center gap-2">
          <button
            onClick={() => handlePageChange(pagination.page - 1)}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
            Page {pagination.page} of {pagination.total_pages} (
            {pagination.total} books)
          </span>

          <button
            onClick={() => handlePageChange(pagination.page + 1)}
            disabled={pagination.page >= pagination.total_pages}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </>
  );
}
