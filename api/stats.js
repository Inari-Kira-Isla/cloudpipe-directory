/**
 * AEO Tracker Stats API
 *
 * Returns aggregated crawler statistics.
 * No PII exposed.
 */

// Shared in-memory store reference (same instance in track.js)
// In production, this would be Vercel KV / Redis
const memStore = globalThis.__aeoStore || { hits: {}, recent: [] };
globalThis.__aeoStore = memStore;

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Aggregate bot stats
  const botStats = {};
  const botMap = {
    gptbot: ['GPTBot', 'ChatGPT-User'],
    claudebot: ['ClaudeBot', 'Anthropic'],
    google: ['Google-Extended', 'Googlebot'],
    perplexity: ['PerplexityBot'],
    bingbot: ['Bingbot'],
    ccbot: ['CCBot'],
    bytespider: ['Bytespider'],
    meta: ['Meta-ExternalAgent', 'FacebookBot'],
  };

  for (const [key, signatures] of Object.entries(botMap)) {
    let hits = 0;
    let lastSeen = null;

    for (const sig of signatures) {
      const sigKey = sig.toLowerCase().replace(/[^a-z0-9]/g, '');
      hits += memStore.hits[sigKey] || 0;
    }

    // Find last seen from recent entries
    for (const entry of memStore.recent) {
      if (entry.bot && signatures.some(s => entry.bot === s)) {
        lastSeen = entry.ts;
        break;
      }
    }

    botStats[key] = { hits, last: lastSeen || 'Never' };
  }

  // Summary
  const totalBotHits = Object.values(memStore.hits).reduce((a, b) => a + b, 0);
  const totalHits = memStore.recent.length;

  res.setHeader('Cache-Control', 'public, max-age=60');
  res.setHeader('Access-Control-Allow-Origin', '*');

  return res.status(200).json({
    ...botStats,
    _summary: {
      totalBotHits,
      totalHits,
      recentCount: memStore.recent.length,
      updatedAt: new Date().toISOString(),
    }
  });
}
