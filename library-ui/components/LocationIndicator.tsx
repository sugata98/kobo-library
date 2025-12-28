import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

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
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Sequential number badge */}
      <Badge
        variant="secondary"
        className="flex items-center justify-center size-5 md:size-6 rounded-full font-semibold text-[10px] md:text-xs shrink-0 p-0"
        title={`Item ${index} of ${total}`}
      >
        {index}
      </Badge>

      {/* Chapter name and progress */}
      <div className="flex-1 min-w-0">
        {chapterName && (
          <div className="text-sm font-medium text-foreground truncate mb-1">
            {chapterName}
          </div>
        )}
        {chapterProgress != null &&
          typeof chapterProgress === "number" &&
          !isNaN(chapterProgress) && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {Math.round(chapterProgress * 100)}%
              </span>
              <Progress
                value={Math.round(chapterProgress * 100)}
                className="flex-1 h-1.5 max-w-[120px]"
              />
            </div>
          )}
      </div>
    </div>
  );
}
