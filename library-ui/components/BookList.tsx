"use client";

import { useState, useEffect } from "react";
import { getBooks, getBookCoverUrl } from "@/lib/api";
import Link from "next/link";

/**
 * Renders a book cover image when available and a styled placeholder otherwise.
 *
 * Fetches a cover URL when `title`, `author`, or `isbn` change, displays the image if the fetch succeeds, hides the placeholder on image load, and shows the placeholder if the image fails to load.
 *
 * @param title - The book title used to locate a cover image.
 * @param author - Optional author name to improve cover lookup.
 * @param isbn - Optional ISBN to improve cover lookup.
 * @returns A JSX element containing either the cover image or a placeholder UI.
 */
function BookCover({
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
    <div className="relative w-full aspect-[2/3] max-h-48 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 overflow-hidden">
      {coverUrl && (
        <img
          src={coverUrl}
          alt={`${title} cover`}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onLoad={(e) => {
            const target = e.target as HTMLImageElement;
            const placeholder = target.parentElement?.querySelector(
              ".cover-placeholder"
            ) as HTMLElement;
            if (placeholder) {
              placeholder.style.display = "none";
            }
          }}
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
      {/* Placeholder when cover image fails to load or is loading */}
      <div className="cover-placeholder absolute inset-0 flex items-center justify-center text-gray-400 dark:text-gray-500">
        <div className="text-center">
          <svg
            className="w-16 h-16 mx-auto mb-2"
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
          <p className="text-xs font-medium">No Cover</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Renders a searchable, paginated grid of book cards with cover images, titles, authors, and progress indicators.
 *
 * When `searchQuery` is non-empty the component performs a server-side search and shows client-side filtered results (pagination is disabled). When `searchQuery` is empty the component fetches paginated books and shows pagination controls.
 *
 * @param searchQuery - Optional search string; when provided triggers server-side search and client-side filtering of results.
 * @returns A React element containing the book grid, loading/error states, and pagination controls (pagination hidden while searching).
 */
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

        // Set pagination info if available
        if (response.pagination) {
          setPagination(response.pagination);
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
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
            Page {pagination.page} of {pagination.total_pages} (
            {pagination.total} books)
          </span>

          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= pagination.total_pages}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </>
  );
}