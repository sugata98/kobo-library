const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/**
 * Trigger backend to sync KoboReader.sqlite from B2.
 * Note: Not currently exposed in UI - backend syncs on startup.
 * Could be used for manual refresh feature in the future.
 */
export async function syncData() {
  const res = await fetch(`${API_BASE_URL}/sync`, {
    method: "POST",
    credentials: "include", // Important: send cookies
  });
  if (!res.ok) throw new Error("Failed to sync data");
  return res.json();
}

export async function getBooks(
  page: number = 1,
  pageSize: number = 10,
  search?: string,
  contentType?: string | null
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (search) {
    params.append("search", search);
  }
  if (contentType) {
    params.append("type", contentType);
  }
  const res = await fetch(`${API_BASE_URL}/books?${params.toString()}`, {
    credentials: "include", // Important: send cookies
  });
  if (!res.ok) throw new Error("Failed to fetch books");
  return res.json();
}

export async function getBookHighlights(bookId: string) {
  const res = await fetch(
    `${API_BASE_URL}/books/${encodeURIComponent(bookId)}/highlights`,
    {
      credentials: "include", // Important: send cookies
    }
  );
  if (!res.ok) throw new Error("Failed to fetch highlights");
  return res.json();
}

export async function getBookMarkups(bookId: string) {
  const res = await fetch(
    `${API_BASE_URL}/books/${encodeURIComponent(bookId)}/markups`,
    {
      credentials: "include", // Important: send cookies
    }
  );
  if (!res.ok) throw new Error("Failed to fetch markups");
  return res.json();
}

export async function getBookDetails(bookId: string) {
  const res = await fetch(
    `${API_BASE_URL}/books/${encodeURIComponent(bookId)}`,
    {
      credentials: "include", // Important: send cookies
    }
  );
  if (!res.ok) throw new Error("Failed to fetch book details");
  return res.json();
}

/**
 * Get book cover URL from backend API.
 *
 * Backend handles:
 * 1. B2 Cache - instant serving from cache
 * 2. ImageUrl from Kobo database (for articles/embedded covers)
 * 3. bookcover-api (Goodreads) - highest quality
 * 4. Open Library API - fallback
 * 5. Google Books API - final fallback
 *
 * Browser HTTP cache handles caching via Cache-Control headers (30 days).
 * No localStorage needed - simpler and more reliable!
 */
export function getBookCoverUrl(
  title: string,
  author?: string,
  isbn?: string,
  imageUrl?: string
): string | null {
  if (!title) return null;

  // Build query parameters for backend endpoint
  const params = new URLSearchParams({
    title: title,
  });

  if (author) {
    params.append("author", author);
  }
  if (isbn) {
    params.append("isbn", isbn);
  }
  if (imageUrl) {
    params.append("image_url", imageUrl);
  }

  // Return the backend URL directly
  // Browser will cache it automatically via Cache-Control headers
  return `${API_BASE_URL}/books/_/cover?${params.toString()}`;
}
