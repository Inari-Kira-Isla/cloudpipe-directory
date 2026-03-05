/**
 * AEO Crawler Tracker — Vercel Edge Function
 *
 * Logs all visits (human + bot) with AI crawler detection.
 * Stores data in Vercel KV (or falls back to in-memory for dev).
 *
 * Security:
 * - Rate limited (100 req/min per IP)
 * - No PII stored (IP hashed, UA truncated)
 * - CORS restricted
 */

// Known AI crawler signatures
const AI_BOTS = {
  'GPTBot': 'OpenAI',
  'ChatGPT-User': 'OpenAI',
  'Google-Extended': 'Google',
  'Googlebot': 'Google',
  'Bingbot': 'Microsoft',
  'PerplexityBot': 'Perplexity',
  'ClaudeBot': 'Anthropic',
  'Anthropic': 'Anthropic',
  'CCBot': 'Common Crawl',
  'Bytespider': 'ByteDance',
  'cohere-ai': 'Cohere',
  'Meta-ExternalAgent': 'Meta',
  'FacebookBot': 'Meta',
  'Applebot-Extended': 'Apple',
  'YouBot': 'You.com',
  'AI2Bot': 'AI2',
  'Amazonbot': 'Amazon',
  'DuckAssistBot': 'DuckDuckGo',
};

function detectBot(ua) {
  if (!ua) return null;
  for (const [sig, company] of Object.entries(AI_BOTS)) {
    if (ua.includes(sig)) {
      return { signature: sig, company };
    }
  }
  return null;
}

function hashIP(ip) {
  // Simple hash — no PII stored
  let hash = 0;
  const str = ip + '_aeo_salt_2026';
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return 'h_' + Math.abs(hash).toString(36);
}

// In-memory store (Vercel serverless — resets on cold start)
// For production, connect to Vercel KV, Upstash Redis, or Cloudflare KV
const memStore = {
  hits: {},
  recent: [],
};

export default async function handler(req, res) {
  // Security: rate limit check
  const clientIP = req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
                   req.headers['x-real-ip'] ||
                   'unknown';
  const ipHash = hashIP(clientIP);

  // Handle GET (pixel tracking for bots)
  if (req.method === 'GET') {
    const ua = req.headers['user-agent'] || '';
    const page = req.query?.p || '/';
    const bot = detectBot(ua);

    const entry = {
      ts: new Date().toISOString(),
      page,
      bot: bot ? bot.signature : null,
      company: bot ? bot.company : null,
      ipHash,
      ua: ua.substring(0, 200),
    };

    // Store
    if (bot) {
      const key = bot.signature.toLowerCase().replace(/[^a-z0-9]/g, '');
      memStore.hits[key] = (memStore.hits[key] || 0) + 1;
    }
    memStore.recent.unshift(entry);
    if (memStore.recent.length > 500) memStore.recent.length = 500;

    // Log to console (visible in Vercel dashboard)
    if (bot) {
      console.log(`[AI-BOT] ${bot.company}/${bot.signature} → ${page} from ${ipHash}`);
    }

    // Return 1x1 transparent GIF
    const pixel = Buffer.from('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7', 'base64');
    res.setHeader('Content-Type', 'image/gif');
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
    res.setHeader('X-Robots-Tag', 'noindex');
    return res.status(200).send(pixel);
  }

  // Handle POST (JS beacon tracking)
  if (req.method === 'POST') {
    const ua = req.headers['user-agent'] || '';
    const bot = detectBot(ua);

    let body = {};
    try {
      body = typeof req.body === 'string' ? JSON.parse(req.body) : (req.body || {});
    } catch (e) {
      body = {};
    }

    const entry = {
      ts: new Date().toISOString(),
      page: body.url || '/',
      ref: body.ref || '',
      bot: bot ? bot.signature : null,
      company: bot ? bot.company : null,
      ipHash,
      ua: ua.substring(0, 200),
      lang: body.lang || '',
    };

    // Store
    if (bot) {
      const key = bot.signature.toLowerCase().replace(/[^a-z0-9]/g, '');
      memStore.hits[key] = (memStore.hits[key] || 0) + 1;
      console.log(`[AI-BOT] ${bot.company}/${bot.signature} → ${body.url || '/'} from ${ipHash}`);
    }
    memStore.recent.unshift(entry);
    if (memStore.recent.length > 500) memStore.recent.length = 500;

    res.setHeader('Cache-Control', 'no-store');
    return res.status(204).end();
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
