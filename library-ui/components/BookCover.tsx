"use client";

import { useState } from "react";
import { getBookCoverUrl } from "@/lib/api";

interface BookCoverProps {
  title: string;
  author?: string;
  isbn?: string;
  imageUrl?: string;
  className?: string;
  iconSize?: string;
  showPlaceholderText?: boolean;
  imageClassName?: string;
}

export default function BookCover({
  title,
  author,
  isbn,
  imageUrl,
  className = "relative w-full aspect-[2/3] max-h-48 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 overflow-hidden",
  iconSize = "w-16 h-16",
  showPlaceholderText = false,
  imageClassName = "w-full h-full object-cover",
}: BookCoverProps) {
  // Get cover URL directly (synchronous, no promises needed)
  const coverUrl = title ? getBookCoverUrl(title, author, isbn, imageUrl) : null;
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleImageLoad = () => {
    setImageLoaded(true);
    setImageError(false);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(false);
  };

  const showPlaceholder = !coverUrl || imageError || !imageLoaded;
  /* eslint-disable @next/next/no-img-element */
  return (
    <div className={className}>
      {coverUrl && (
        <img
          key={`${title}-${author}-${isbn}-${coverUrl}`}
          src={coverUrl}
          alt={`${title} cover`}
          className={imageClassName}
          onLoad={handleImageLoad}
          onError={handleImageError}
          style={{ display: showPlaceholder ? "none" : "block" }}
        />
      )}
      {/* Placeholder when cover image fails to load or is loading */}
      {showPlaceholder && (
        <div className="cover-placeholder absolute inset-0 flex items-center justify-center text-gray-400 dark:text-gray-500">
          <div className="text-center">
            <svg
              className={`${iconSize} mx-auto ${
                showPlaceholderText ? "mb-2" : ""
              }`}
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
            {showPlaceholderText && (
              <p className="text-xs font-medium">No Cover</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
