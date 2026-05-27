export function buildTrend(trendArray) {
  return (trendArray || []).map((score, index) => ({
    period: `P${index + 1}`,
    score
  }));
}

export function buildDistribution(items, key) {
  return Object.values(
    (items || []).reduce((acc, item) => {
      const label = item[key] || "Unknown";
      acc[label] = acc[label] || { name: label, value: 0 };
      acc[label].value += 1;
      return acc;
    }, {})
  );
}
