/**
 * Branding Constants
 * Single source of truth for all app branding and messaging
 */

export const BRANDING = {
  // App Identity
  name: "Readr",
  domain: "readr.space",

  // Taglines & Descriptions
  tagline: "Your personal space to revisit and connect reading highlights",
  description:
    "Readr is a personal space to revisit and connect your reading highlights and annotations. Sync, organize, and reflect on insights from your reading journey.",
  shortDescription:
    "Revisit and connect your reading highlights and annotations",

  // Meta
  keywords: [
    "reading highlights",
    "annotations",
    "notes",
    "reading reflection",
    "book insights",
    "kobo sync",
  ],

  // Messaging Guidelines
  positioning: {
    focus: "Revisiting, reflecting on, and connecting highlights",
    avoid: "Reading books, ebook consumption, book reader functionality",
    tone: "Calm, minimal, reader-first",
  },

  // UI Copy
  ui: {
    backToLibrary: "← Back to Library",
    searchPlaceholder: "Search books...",
    loadingBooks: "Loading books...",
    loadingDetails: "Loading details...",
    noHighlights: "No highlights found.",
    noMarkups: "No markups found.",
  },
} as const;
