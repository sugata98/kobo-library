const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/**
 * Trigger a server-side data synchronization.
 *
 * @returns The JSON payload returned by the sync endpoint.
 * @throws Error if the sync request fails (non-OK response).
 */
export async function syncData() {
  const res = await fetch(`${API_BASE_URL}/sync`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to sync data");
  return res.json();
}

/**
 * Fetches a paginated list of books from the API.
 *
 * @param page - 1-based page number to request (defaults to 1)
 * @param pageSize - Number of items per page (defaults to 10)
 * @param search - Optional search query to filter books by title, author, or other searchable fields
 * @returns The parsed JSON response containing the books and pagination metadata
 */
export async function getBooks(
  page: number = 1,
  pageSize: number = 10,
  search?: string
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (search) {
    params.append("search", search);
  }
  const res = await fetch(`${API_BASE_URL}/books?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch books");
  return res.json();
}

/**
 * Fetches the highlights for a book identified by `bookId`.
 *
 * @param bookId - The book identifier to include in the API request path
 * @returns The parsed JSON response containing the book's highlights
 */
export async function getBookHighlights(bookId: string) {
  const res = await fetch(
    `${API_BASE_URL}/books/${encodeURIComponent(bookId)}/highlights`
  );
  if (!res.ok) throw new Error("Failed to fetch highlights");
  return res.json();
}

/**
 * Fetches markups for a book identified by its ID.
 *
 * @returns The parsed JSON response containing the book's markups.
 * @throws Error if the HTTP response is not OK.
 */
export async function getBookMarkups(bookId: string) {
  const res = await fetch(
    `${API_BASE_URL}/books/${encodeURIComponent(bookId)}/markups`
  );
  if (!res.ok) throw new Error("Failed to fetch markups");
  return res.json();
}

/**
 * Fetches the details for a specific book by its identifier.
 *
 * @param bookId - The book identifier to include in the request path; it will be URL-encoded.
 * @returns The parsed JSON object containing the book's details.
 * @throws Error if the HTTP response has a non-OK status.
 */
export async function getBookDetails(bookId: string) {
  const res = await fetch(
    `${API_BASE_URL}/books/${encodeURIComponent(bookId)}`
  );
  if (!res.ok) throw new Error("Failed to fetch book details");
  return res.json();
}

/**
 * Fetch book cover with caching strategy:
 * 1. Check LocalStorage cache first
 * 2. If ISBN exists, construct Open Library URL directly (no API call)
 * 3. If no ISBN, search Google Books API by title
 * 4. Cache results in LocalStorage
 */
// In-flight request cache to prevent duplicate simultaneous calls
const inFlightRequests = new Map<string, Promise<string | null>>();

/**
 * Retrieve a book cover image URL using ISBN, Google Books lookup, and a local cache.
 *
 * Attempts to return a cached cover URL first. If an ISBN is provided and valid (10 or 13 digits),
 * constructs an Open Library cover URL. Otherwise queries the Google Books API for a cover image.
 * Successful URLs and failed lookups are cached in localStorage when available, and concurrent
 * requests for the same book are deduplicated.
 *
 * @param title - The book title; if missing, the function returns `null`
 * @param author - Optional author name to refine Google Books lookup
 * @param isbn - Optional ISBN (may include dashes/spaces); used to build an Open Library cover URL when it cleans to 10 or 13 digits
 * @returns The cover image URL as a `string` if found, or `null` if no cover could be determined
 */
export async function getBookCoverUrl(
  title: string,
  author?: string,
  isbn?: string
): Promise<string | null> {
  if (!title) return null;

  // Create cache key from title and author
  const cacheKey = `book_cover_${title}_${author || ""}`;

  // Check LocalStorage cache first
  try {
    const cached = localStorage.getItem(cacheKey);
    // Check for cached URL (starts with http) or cached failure (empty string means failed)
    if (cached !== null) {
      if (cached === "") {
        // Cached failure - don't retry
        return null;
      }
      if (cached.startsWith("http")) {
        return cached;
      }
    }
  } catch (e) {
    // LocalStorage might not be available (SSR, private browsing, etc.)
    console.debug("LocalStorage not available:", e);
  }

  // Check if there's already an in-flight request for this book
  const requestKey = `${title}_${author || ""}_${isbn || ""}`;
  if (inFlightRequests.has(requestKey)) {
    return inFlightRequests.get(requestKey)!;
  }

  // Create the request promise
  const requestPromise = (async () => {
    let coverUrl: string | null = null;

    // Strategy 1: If ISBN exists, construct Open Library URL directly (no API call)
    if (isbn) {
      // Clean ISBN (remove dashes, spaces)
      const cleanIsbn = isbn.replace(/[-\s]/g, "");
      if (cleanIsbn.length === 10 || cleanIsbn.length === 13) {
        coverUrl = `https://covers.openlibrary.org/b/isbn/${cleanIsbn}-L.jpg`;
        // Cache the result
        try {
          localStorage.setItem(cacheKey, coverUrl);
        } catch (e) {
          console.debug("Failed to cache cover URL:", e);
        }
        return coverUrl;
      }
    }

    // Strategy 2: Fallback to Google Books API search by title
    try {
      coverUrl = await fetchFromGoogleBooks(title, author);
      if (coverUrl) {
        // Cache the result
        try {
          localStorage.setItem(cacheKey, coverUrl);
        } catch (e) {
          console.debug("Failed to cache cover URL:", e);
        }
        return coverUrl;
      }
    } catch (e) {
      console.debug("Google Books fetch failed:", e);
      // Return null on error
    }

    // Cache null result to avoid repeated failed API calls
    try {
      localStorage.setItem(cacheKey, "");
    } catch {
      // Ignore cache errors
    }

    return null;
  })();

  // Store the in-flight request
  inFlightRequests.set(requestKey, requestPromise);

  // Clean up after request completes
  requestPromise.finally(() => {
    inFlightRequests.delete(requestKey);
  });

  return requestPromise;
}

/**
 * Finds a book cover image URL on Google Books using the given title and optional author.
 *
 * Prefers larger image sizes when multiple are available and converts returned URLs to `https`.
 *
 * @param title - The book title to query
 * @param author - Optional author name to narrow the query
 * @returns The cover image URL (using `https`) if a suitable image is found, `null` otherwise (including when no image is available, the request is rate limited, or an error occurs)
 */
async function fetchFromGoogleBooks(
  title: string,
  author?: string
): Promise<string | null> {
  try {
    let query = `intitle:${title}`;
    if (author) {
      query += `+inauthor:${author}`;
    }

    const searchUrl = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(
      query
    )}&maxResults=1`;

    // Add timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(searchUrl, {
      signal: controller.signal,
      cache: "default", // Changed from 'force-cache' - browser cache handles this
    });

    clearTimeout(timeoutId);

    // Handle rate limiting (429) - don't retry immediately
    if (response.status === 429) {
      console.debug("Google Books API rate limited");
      return null;
    }

    if (!response.ok) return null;

    const data = await response.json();
    if (!data.items || data.items.length === 0) return null;

    const volume = data.items[0];
    const imageLinks = volume.volumeInfo?.imageLinks;
    if (!imageLinks) return null;

    // Try different sizes, prefer larger
    const sizes = ["large", "medium", "small", "thumbnail", "smallThumbnail"];
    for (const size of sizes) {
      if (imageLinks[size]) {
        return imageLinks[size].replace("http://", "https://");
      }
    }

    return null;
  } catch {
    // If Google Books fails, return null
    return null;
  }
}