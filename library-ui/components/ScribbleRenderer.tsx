import { useState, useEffect, useRef } from "react";

export default function ScribbleRenderer({ hex }: { hex: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [parsedPoints, setParsedPoints] = useState<number[]>([]);

  useEffect(() => {
    if (!hex) return;

    // Convert hex to 32-bit integers (Big Endian)
    // We start scanning after the textual header.
    // The textual header contains "StartKey", "QVector<int>", "EndKey".
    // "EndKey" seems to be near the end of the header section.

    // Heuristic: Look for the longest sequence of valid coordinates.
    // Coordinates typically are positive integers (0-2000).
    // Let's convert the whole buffer to int32s and find the longest chain of "reasonable" points.

    const bytes = new Uint8Array(
      hex.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16))
    );
    const view = new DataView(bytes.buffer);
    const ints: number[] = [];

    for (let i = 0; i < bytes.length - 4; i += 4) {
      ints.push(view.getInt32(i, false)); // Big Endian
    }

    // Filter for point-like data.
    // Valid Kobo points are usually > 0 and < 3000 (screen resolution).
    // We look for a sequence of [x, y, x, y...]

    // Find the sequence of "points"
    // Usually preceded by the length of the vector.

    let bestSequence: number[] = [];
    let currentSequence: number[] = [];

    for (let i = 0; i < ints.length; i++) {
      const val = ints[i];
      // Heuristic for coordinate
      if (val > 0 && val < 5000) {
        currentSequence.push(val);
      } else {
        if (currentSequence.length > bestSequence.length) {
          bestSequence = currentSequence;
        }
        currentSequence = [];
      }
    }

    // Check trailing sequence
    if (currentSequence.length > bestSequence.length) {
      bestSequence = currentSequence;
    }

    // Defer setState to avoid synchronous setState in effect
    const timeoutId = setTimeout(() => {
      setParsedPoints(bestSequence);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [hex]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || parsedPoints.length < 4) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Auto-scale
    const xs = parsedPoints.filter((_, i) => i % 2 === 0);
    const ys = parsedPoints.filter((_, i) => i % 2 === 1);

    if (xs.length === 0 || ys.length === 0) return;

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    const width = maxX - minX || 100;
    const height = maxY - minY || 100;

    canvas.width = width + 20;
    canvas.height = height + 20;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.strokeStyle = "red";
    ctx.lineWidth = 2;

    // Draw points
    // Note: Kobo scribbles might be multiple strokes.
    // Our naive parser treats it as one long stroke for now.
    // If there are large jumps, we might want to split them.

    ctx.moveTo(parsedPoints[0] - minX + 10, parsedPoints[1] - minY + 10);

    for (let i = 2; i < parsedPoints.length; i += 2) {
      const x = parsedPoints[i] - minX + 10;
      const y = parsedPoints[i + 1] - minY + 10;

      // Simple distance check to detect new strokes (pen lift)
      // If distance is huge, maybe skip lineTo
      const prevX = parsedPoints[i - 2] - minX + 10;
      const prevY = parsedPoints[i - 1] - minY + 10;
      const dist = Math.sqrt(Math.pow(x - prevX, 2) + Math.pow(y - prevY, 2));

      if (dist > 500) {
        // Arbitrary threshold for "pen lift"
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }

    ctx.stroke();
  }, [parsedPoints]);

  if (parsedPoints.length === 0)
    return <div className="text-xs text-gray-400">No drawing data found</div>;

  return (
    <div className="border rounded bg-white p-2">
      <canvas ref={canvasRef} className="border border-gray-100 bg-white" />
      <div className="text-xs text-gray-400 mt-1">
        Points found: {parsedPoints.length / 2}
      </div>
    </div>
  );
}
