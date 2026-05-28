/**
 * Word Cloud Layout Engine
 * Spiral-based placement algorithm with AABB collision detection.
 */

const PADDING = 6;
const CHAR_WIDTH_FACTOR = 0.58;
const LINE_HEIGHT_FACTOR = 1.25;
const Y_FLATTEN = 0.55;

/** Fisher-Yates shuffle (returns a new array) */
function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** AABB overlap check with padding */
function overlaps(a, b) {
  return !(
    a.x + a.w + PADDING <= b.x ||
    b.x + b.w + PADDING <= a.x ||
    a.y + a.h + PADDING <= b.y ||
    b.y + b.h + PADDING <= a.y
  );
}

/** Compute font size linearly from weight (1–10) */
function fontSize(weight, minFS, maxFS) {
  return minFS + ((weight - 1) / 9) * (maxFS - minFS);
}

/**
 * Run the spiral placement algorithm.
 * 1. Assign font sizes, shuffle for visual randomness
 * 2. Sort by weight descending so large words place first
 * 3. For each word, spiral outward from (0,0) to find a non-overlapping spot
 */
export function computeLayout(words, minFontSize, maxFontSize) {
  const items = words.map((w) => {
    const fs = fontSize(w.weight, minFontSize, maxFontSize);
    return {
      text: w.text,
      weight: w.weight,
      fontSize: fs,
      w: w.text.length * fs * CHAR_WIDTH_FACTOR,
      h: fs * LINE_HEIGHT_FACTOR,
      x: 0,
      y: 0,
    };
  });

  // Shuffle first so same-weight words get random visual order
  const shuffled = shuffle(items);
  // Then stable-sort by weight descending so heaviest words place first (center)
  shuffled.sort((a, b) => b.weight - a.weight);

  const placed = [];

  for (const item of shuffled) {
    let didPlace = false;
    const angleOffset = Math.random() * Math.PI * 2;

    for (let ring = 0; ring <= 200; ring++) {
      const radius = ring * 4;
      const steps = Math.max(6, Math.floor(ring * 6));
      for (let s = 0; s < steps; s++) {
        const angle = angleOffset + (s / steps) * Math.PI * 2;
        const cx = Math.cos(angle) * radius;
        const cy = Math.sin(angle) * radius * Y_FLATTEN;
        const candidate = {
          ...item,
          x: cx - item.w / 2,
          y: cy - item.h / 2,
        };
        if (!placed.some((p) => overlaps(candidate, p))) {
          placed.push(candidate);
          didPlace = true;
          break;
        }
      }
      if (didPlace) break;
    }
    if (!didPlace) {
      placed.push(item);
    }
  }

  // Normalize coordinates so the top-left of the cloud starts at (0,0)
  const minX = Math.min(...placed.map((p) => p.x));
  const minY = Math.min(...placed.map((p) => p.y));
  for (const p of placed) {
    p.x -= minX;
    p.y -= minY;
  }

  const cloudWidth = Math.max(...placed.map((p) => p.x + p.w));
  const cloudHeight = Math.max(...placed.map((p) => p.y + p.h));

  return { placed, cloudWidth, cloudHeight };
}
