/** Map API terms (count-based) to { text, weight } for the word cloud. */
export function termsToWords(terms) {
  if (!terms.length) return [];
  const maxCount = Math.max(...terms.map((t) => t.count));
  const minCount = Math.min(...terms.map((t) => t.count));
  const range = maxCount - minCount || 1;
  return terms.map((t) => ({
    text: t.term.charAt(0).toUpperCase() + t.term.slice(1),
    count: t.count,
    weight: 1 + ((t.count - minCount) / range) * 9,
  }));
}
