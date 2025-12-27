/**
 * Branding Constants
 * Single source of truth for all app branding and messaging
 */

export const BRANDING = {
  // App Identity
  name: "Readr",
  domain: "readr.space",

  // Taglines & Descriptions
  tagline: "Where your reading highlights live",
  description:
    "Readr is a personal space where your reading highlights and annotations live. Revisit, connect, and reflect on insights from your reading journey.",
  shortDescription: "A home for your reading highlights and annotations",

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
    searchPlaceholder: "Search by title or author...",
    noHighlights: "No highlights yet.",
    noMarkups: "No markups yet.",
  },
} as const;
