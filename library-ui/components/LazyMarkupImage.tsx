"use client";

import React, { useState, useEffect, useRef } from "react";
import { Spinner } from "@/components/ui/spinner";

interface LazyMarkupImageProps {
  markupId: string;
  priority?: boolean; // Load immediately without lazy loading
  preloadMargin?: string; // How far before viewport to start loading
  overlay?: React.ReactNode; // Optional overlay content to display on top
}

// Use the backend proxy endpoints
const getSvgUrl = (markupId: string) =>
  `${
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
  }/markup/${markupId}/svg`;

const getJpgUrl = (markupId: string) =>
  `${
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"
  }/markup/${markupId}/jpg`;

/* eslint-disable @next/next/no-img-element */
export default function LazyMarkupImage({
  markupId,
  priority = false,
  preloadMargin = "400px", // Larger margin for markups since they're bigger
  overlay,
}: LazyMarkupImageProps) {
  const [shouldLoad, setShouldLoad] = useState(priority);
  const [jpgLoaded, setJpgLoaded] = useState(false);
  const [svgLoaded, setSvgLoaded] = useState(false);
  const [jpgError, setJpgError] = useState(false);
  const [svgError, setSvgError] = useState(false);
  const [showFallback, setShowFallback] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (priority || !containerRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setShouldLoad(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: preloadMargin, // Start loading before entering viewport
        threshold: 0.01,
      }
    );

    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, [priority, preloadMargin]);

  const handleJpgLoad = () => {
    setJpgLoaded(true);
  };

  const handleJpgError = () => {
    setJpgError(true);
    setShowFallback(true);
  };

  const handleSvgLoad = () => {
    setSvgLoaded(true);
  };

  const handleSvgError = () => {
    setSvgError(true);
  };

  return (
    <div
      ref={containerRef}
      className="rounded-lg overflow-hidden relative w-full"
    >
      {/* Optional overlay content */}
      {overlay && (
        <div className="absolute bottom-0 left-0 right-0 z-40 pointer-events-auto">
          {overlay}
        </div>
      )}

      {!showFallback && (
        <div className="relative min-h-[200px] bg-muted/20">
          {/* Loader - stays in background, gets covered by JPG when it streams in */}
          {(!shouldLoad || (!jpgLoaded && !jpgError)) && (
            <div className="absolute inset-0 w-full min-h-[200px] bg-linear-to-br from-muted to-muted/80 animate-pulse rounded-lg flex items-center justify-center z-0">
              <Spinner className="size-8 text-primary" />
              {!shouldLoad && (
                <span className="absolute bottom-4 text-xs text-muted-foreground">
                  Loading when visible...
                </span>
              )}
            </div>
          )}

          {/* JPG Background - progressively loads and covers the loader as it streams */}
          {shouldLoad && (
            <img
              src={getJpgUrl(markupId)}
              alt="Page"
              className="max-w-full h-auto block relative z-20"
              onLoad={handleJpgLoad}
              onError={handleJpgError}
              loading="eager"
              decoding="async"
            />
          )}

          {/* SVG Overlay (positioned absolutely on top) - waits for JPG to load */}
          {jpgLoaded && !svgError && (
            <img
              src={getSvgUrl(markupId)}
              alt="Markup"
              className="absolute top-0 left-0 w-full h-full pointer-events-none transition-opacity duration-300 z-30"
              style={{ mixBlendMode: "normal", opacity: svgLoaded ? 1 : 0 }}
              onLoad={handleSvgLoad}
              onError={handleSvgError}
              loading="eager"
            />
          )}
        </div>
      )}

      {/* Fallback message */}
      {showFallback && (
        <div className="text-xs text-muted-foreground text-center p-4">
          Images not found in B2.
          <br />
          (ID: {markupId})
        </div>
      )}
    </div>
  );
}
