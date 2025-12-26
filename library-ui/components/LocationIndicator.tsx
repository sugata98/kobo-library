interface LocationIndicatorProps {
  index: number; // Sequential index (1-based) of the item
  total: number; // Total number of items
  chapterName?: string | null; // Chapter name (e.g., "CHAPTER 8: DESIGN A URL SHORTENER")
  chapterProgress?: number | null; // Chapter-relative progress (0-1)
  className?: string;
}

/**
 * Displays a sequential position indicator for highlights/markups
 * Shows index number, chapter name, and optional chapter progress
 */
export default function LocationIndicator({
  index,
  total,
  chapterName,
  chapterProgress,
  className = "",
}: LocationIndicatorProps) {
  // Determine progress bar color based on chapter progress
  let progressBarColor = "bg-blue-500";

  if (chapterProgress !== null && chapterProgress !== undefined) {
    if (chapterProgress < 0.33) {
      progressBarColor = "bg-green-500";
    } else if (chapterProgress < 0.66) {
      progressBarColor = "bg-yellow-500";
    } else {
      progressBarColor = "bg-purple-500";
    }
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Sequential number badge - simple gray */}
      <div
        className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-semibold text-sm shrink-0 border border-gray-200 dark:border-gray-700"
        title={`Item ${index} of ${total}`}
      >
        {index}
      </div>

      {/* Chapter name and progress */}
      <div className="flex-1 min-w-0">
        {chapterName && (
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate mb-1">
            {chapterName}
          </div>
        )}
        {chapterProgress != null &&
          typeof chapterProgress === "number" &&
          !isNaN(chapterProgress) && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                {Math.round(chapterProgress * 100)}%
              </span>
              <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700 max-w-[120px]">
                <div
                  className={`h-full ${progressBarColor} transition-all duration-300`}
                  style={{ width: `${Math.round(chapterProgress * 100)}%` }}
                />
              </div>
            </div>
          )}
      </div>
    </div>
  );
}
