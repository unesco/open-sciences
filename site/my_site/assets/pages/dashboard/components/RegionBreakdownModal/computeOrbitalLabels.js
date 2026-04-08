/**
 * Computes orbital floating-label positions around a doughnut ring.
 * Returns an array of items with pre-resolved (lx, ly) coordinates,
 * collision-spread vertically so labels don't overlap.
 *
 * answerEntries: [{ name, count, colorIdx }]
 * total:         sum of all counts
 * config:        override { CX, CY, R, LABEL_H, MIN_GAP }
 */

const DEFAULTS = {
  CX:      130,   // half the wrapper width
  CY:      120,   // half the wrapper height
  R:       58,    // orbit radius
  LABEL_H: 46,    // assumed label height for collision resolution
  MIN_GAP: 6,     // minimum gap between stacked labels
};

export function computeOrbitalLabels(answerEntries, total, config = {}) {
  const { CX, CY, R, LABEL_H, MIN_GAP } = { ...DEFAULTS, ...config };

  let cumDeg = -90; // start at the top of the circle
  const items = answerEntries.map(({ name, count, colorIdx }, i) => {
    const pct     = total ? Math.round((count / total) * 100) : 0;
    const frac    = total > 0 ? count / total : 0;
    const spanDeg = frac * 360;
    const midDeg  = cumDeg + spanDeg / 2;
    cumDeg       += spanDeg;
    const midRad  = (midDeg * Math.PI) / 180;
    return {
      name, pct, i, colorIdx,
      lx:      CX + R * Math.cos(midRad),
      ly:      CY + R * Math.sin(midRad),
      onRight: Math.cos(midRad) >= 0,
    };
  });

  // Push overlapping labels apart vertically, clamp within bounds
  const MIN_Y = 16;
  const MAX_Y = CY * 2 - 16;
  [true, false].forEach((side) => {
    const grp = items.filter((d) => d.onRight === side).sort((a, b) => a.ly - b.ly);
    for (let iter = 0; iter < 40; iter++) {
      for (let j = 1; j < grp.length; j++) {
        const a = grp[j - 1];
        const b = grp[j];
        const overlap = (a.ly + LABEL_H + MIN_GAP) - b.ly;
        if (overlap > 0) { a.ly -= overlap / 2; b.ly += overlap / 2; }
      }
      grp.forEach((d) => { d.ly = Math.max(MIN_Y, Math.min(MAX_Y, d.ly)); });
    }
  });

  return items;
}
