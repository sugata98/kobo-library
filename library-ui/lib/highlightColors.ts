/**
 * Kobo Highlight Color Mapping
 * Maps Kobo's color values to Tailwind CSS classes and hex colors
 */

export type HighlightColorValue = 0 | 1 | 3 | null | undefined;

export interface HighlightColorConfig {
  name: string;
  borderClass: string;
  bgClass: string;
  textClass: string;
  hex: string;
}

/**
 * Color mapping based on Kobo's highlight system:
 * - 0: Yellow (default)
 * - 1: Red
 * - 3: Blue
 */
export const HIGHLIGHT_COLORS: Record<number, HighlightColorConfig> = {
  0: {
    name: "Yellow",
    borderClass: "border-yellow-500",
    bgClass: "bg-yellow-50 dark:bg-yellow-950/20",
    textClass: "text-yellow-900 dark:text-yellow-100",
    hex: "#eab308",
  },
  1: {
    name: "Red",
    borderClass: "border-red-500",
    bgClass: "bg-red-50 dark:bg-red-950/20",
    textClass: "text-red-900 dark:text-red-100",
    hex: "#ef4444",
  },
  3: {
    name: "Blue",
    borderClass: "border-blue-500",
    bgClass: "bg-blue-50 dark:bg-blue-950/20",
    textClass: "text-blue-900 dark:text-blue-100",
    hex: "#3b82f6",
  },
};

/**
 * Get color configuration for a highlight
 * Falls back to primary color if no color is specified
 */
export function getHighlightColor(
  color: HighlightColorValue
): HighlightColorConfig {
  if (color !== null && color !== undefined && color in HIGHLIGHT_COLORS) {
    return HIGHLIGHT_COLORS[color];
  }

  // Default fallback to primary/neutral
  return {
    name: "Default",
    borderClass: "border-primary",
    bgClass: "bg-muted/50",
    textClass: "text-foreground",
    hex: "#8b5cf6", // fallback hex
  };
}

/**
 * Get a human-readable color name
 */
export function getHighlightColorName(color: HighlightColorValue): string {
  return getHighlightColor(color).name;
}
