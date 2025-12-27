/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect } from "react";
import { getBooks } from "@/lib/api";
import Link from "next/link";
import BookCover from "./BookCover";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { BRANDING } from "@/lib/branding";

export default function BookList({
  searchQuery = "",
  contentType = null,
}: {
  searchQuery?: string;
  contentType?: string | null;
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

  // Reset to page 1 when content type changes
  useEffect(() => {
    setCurrentPage(1);
  }, [contentType]);

  // Fetch paginated books
  useEffect(() => {
    if (searchQuery) return; // Don't fetch paginated when searching

    let cancelled = false;

    (async () => {
      setLoading(true);
      try {
        const response = await getBooks(currentPage, pageSize, undefined, contentType);

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
  }, [currentPage, searchQuery, contentType]);

  // When searching, use server-side search
  useEffect(() => {
    if (searchQuery) {
      setSearchLoading(true);
      getBooks(1, 100, searchQuery, contentType) // Use server-side search with max page size
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
  }, [searchQuery, contentType]);

  if (error) return <div className="text-destructive">Error: {error}</div>;

  // Use server-filtered results directly when searching, paginated results otherwise
  const displayBooks = searchQuery ? allBooksForSearch : books;

  const handlePageChange = (newPage: number) => {
    // Request the intended page but don't update state directly
    // State will be updated from the API response to keep it in sync
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Skeleton loader component
  const BookSkeleton = () => (
    <Card className="overflow-hidden flex flex-col h-full">
      <Skeleton className="w-full aspect-[2/3]" />
      <CardContent className="p-0 pt-4 px-4 pb-4 flex-1 flex flex-col">
        <Skeleton className="h-6 w-full mb-2" />
        <Skeleton className="h-6 w-3/4 mb-1" />
        <Skeleton className="h-4 w-1/2 mb-3" />
        <div className="space-y-2 mt-auto">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-1.5 w-full" />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {(loading || searchLoading) &&
          Array.from({ length: pageSize }).map((_, index) => (
            <BookSkeleton key={`skeleton-${index}`} />
          ))}

        {!(loading || searchLoading) && displayBooks.map((book) => (
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
                <div className="space-y-2 mt-auto">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-medium text-foreground">
                      {Math.round(book.___PercentRead || 0)}%
                    </span>
                  </div>
                  <Progress
                    value={Math.round(book.___PercentRead || 0)}
                    className="h-1.5"
                  />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Pagination Controls - Only show when not searching */}
      {!searchQuery && !(loading || searchLoading) && pagination.total_pages > 1 && (
        <div className="mt-8 space-y-2">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                />
              </PaginationItem>

              {/* First page */}
              {pagination.page > 2 && (
                <PaginationItem>
                  <PaginationLink onClick={() => handlePageChange(1)}>
                    1
                  </PaginationLink>
                </PaginationItem>
              )}

              {/* Ellipsis before current */}
              {pagination.page > 3 && (
                <PaginationItem>
                  <PaginationEllipsis />
                </PaginationItem>
              )}

              {/* Previous page */}
              {pagination.page > 1 && (
                <PaginationItem>
                  <PaginationLink
                    onClick={() => handlePageChange(pagination.page - 1)}
                  >
                    {pagination.page - 1}
                  </PaginationLink>
                </PaginationItem>
              )}

              {/* Current page */}
              <PaginationItem>
                <PaginationLink isActive>{pagination.page}</PaginationLink>
              </PaginationItem>

              {/* Next page */}
              {pagination.page < pagination.total_pages && (
                <PaginationItem>
                  <PaginationLink
                    onClick={() => handlePageChange(pagination.page + 1)}
                  >
                    {pagination.page + 1}
                  </PaginationLink>
                </PaginationItem>
              )}

              {/* Ellipsis after current */}
              {pagination.page < pagination.total_pages - 2 && (
                <PaginationItem>
                  <PaginationEllipsis />
                </PaginationItem>
              )}

              {/* Last page */}
              {pagination.page < pagination.total_pages - 1 && (
                <PaginationItem>
                  <PaginationLink
                    onClick={() => handlePageChange(pagination.total_pages)}
                  >
                    {pagination.total_pages}
                  </PaginationLink>
                </PaginationItem>
              )}

              <PaginationItem>
                <PaginationNext
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page >= pagination.total_pages}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}
    </>
  );
}
