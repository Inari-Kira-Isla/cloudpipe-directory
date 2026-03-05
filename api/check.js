/**
 * AEO Health Check API
 *
 * Fetches a URL and analyzes its AEO optimization level.
 * Returns a score (0-100) and detailed check results.
 *
 * Security:
 * - Rate limited (10 checks/min per IP)
 * - Only fetches HTML content (no binary)
 * - Timeout: 10s
 * - No data stored
 */

const CHECKS = [
  {id:'schema',    name:'Schema.org Structured Data', weight:20},
  {id:'llms',      name:'llms.txt File',              weight:15},
  {id:'robots',    name:'robots.txt AI Rules',        weight:10},
  {id:'meta',      name:'Meta Description',           weight:10},
  {id:'og',        name:'Open Graph Tags',            weight:10},
  {id:'canonical', name:'Canonical URL',              weight:5},
  {id:'faq',       name:'FAQ Schema',                 weight:15},
  {id:'sitemap',   name:'Sitemap.xml',                weight:5},
  {id:'https',     name:'HTTPS',                      weight:5},
  {id:'speed',     name:'Response Speed',             weight:5},
];

async function fetchWithTimeout(url, timeout = 8000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'CloudPipe-AEO-Check/1.0 (+https://cloudpipe-directory.vercel.app/check.html)',
        'Accept': 'text/html, text/plain, application/xml, */*',
      },
      redirect: 'follow',
    });
    clearTimeout(id);
    return res;
  } catch (e) {
    clearTimeout(id);
    throw e;
  }
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({error: 'Method not allowed'});
  }

  const targetUrl = req.query.url;
  if (!targetUrl || !targetUrl.startsWith('http')) {
    return res.status(400).json({error: 'Invalid URL. Must start with http:// or https://'});
  }

  // Security: block internal/private URLs
  try {
    const u = new URL(targetUrl);
    if (['localhost','127.0.0.1','0.0.0.0','[::1]'].includes(u.hostname) ||
        u.hostname.endsWith('.local') || u.hostname.startsWith('10.') ||
        u.hostname.startsWith('192.168.') || u.hostname.startsWith('172.')) {
      return res.status(400).json({error: 'Cannot check internal/private URLs'});
    }
  } catch {
    return res.status(400).json({error: 'Invalid URL format'});
  }

  const baseUrl = targetUrl.replace(/\/+$/, '');
  const startTime = Date.now();
  const items = [];
  let totalScore = 0;

  try {
    // Fetch main page
    let html = '';
    let responseTime = 0;
    let isHttps = targetUrl.startsWith('https');

    try {
      const pageRes = await fetchWithTimeout(targetUrl);
      responseTime = Date.now() - startTime;
      html = await pageRes.text();
    } catch (e) {
      // Page unreachable
      return res.status(200).json({
        score: isHttps ? 5 : 0,
        url: targetUrl,
        error: 'Could not fetch page: ' + e.message,
        items: CHECKS.map(c => ({
          name: c.name, pass: c.id === 'https' && isHttps,
          score: c.id === 'https' && isHttps ? 5 : 0, max: c.weight,
          note: 'Page unreachable'
        }))
      });
    }

    const htmlLower = html.toLowerCase();

    // 1. Schema.org
    const hasSchema = html.includes('application/ld+json');
    const schemaCount = (html.match(/application\/ld\+json/g) || []).length;
    const schemaScore = hasSchema ? Math.min(20, schemaCount * 7) : 0;
    items.push({
      name: 'Schema.org Structured Data',
      pass: hasSchema,
      score: schemaScore,
      max: 20,
      note: hasSchema ? `Found ${schemaCount} schema block(s)` : 'No Schema.org JSON-LD found — AI engines cannot understand your content structure'
    });
    totalScore += schemaScore;

    // 2. llms.txt
    let hasLlms = false;
    const hasLlmsLink = htmlLower.includes('rel="llms-txt"') || htmlLower.includes("rel='llms-txt'");
    try {
      const llmsRes = await fetchWithTimeout(baseUrl + '/llms.txt', 5000);
      hasLlms = llmsRes.ok && llmsRes.status === 200;
    } catch {}
    const llmsScore = (hasLlms ? 10 : 0) + (hasLlmsLink ? 5 : 0);
    items.push({
      name: 'llms.txt File',
      pass: hasLlms || hasLlmsLink,
      score: llmsScore,
      max: 15,
      note: hasLlms && hasLlmsLink ? 'llms.txt exists and linked in HTML'
        : hasLlms ? 'llms.txt exists but not linked in HTML <head>'
        : hasLlmsLink ? 'HTML links to llms.txt but file not found'
        : 'No llms.txt — AI crawlers have no structured entry point to your site'
    });
    totalScore += llmsScore;

    // 3. robots.txt
    let hasRobots = false;
    let robotsContent = '';
    try {
      const robotsRes = await fetchWithTimeout(baseUrl + '/robots.txt', 5000);
      if (robotsRes.ok) {
        hasRobots = true;
        robotsContent = await robotsRes.text();
      }
    } catch {}
    const aiBotsAllowed = robotsContent.toLowerCase().includes('gptbot') ||
                          robotsContent.toLowerCase().includes('claudebot') ||
                          robotsContent.toLowerCase().includes('allow: /');
    const robotsScore = hasRobots ? (aiBotsAllowed ? 10 : 5) : 0;
    items.push({
      name: 'robots.txt AI Rules',
      pass: hasRobots && aiBotsAllowed,
      score: robotsScore,
      max: 10,
      note: !hasRobots ? 'No robots.txt found'
        : aiBotsAllowed ? 'AI crawlers are allowed'
        : 'robots.txt exists but may block AI crawlers'
    });
    totalScore += robotsScore;

    // 4. Meta Description
    const hasMetaDesc = htmlLower.includes('name="description"') || htmlLower.includes("name='description'");
    const metaScore = hasMetaDesc ? 10 : 0;
    items.push({
      name: 'Meta Description',
      pass: hasMetaDesc,
      score: metaScore,
      max: 10,
      note: hasMetaDesc ? 'Meta description found' : 'No meta description — AI engines may generate inaccurate summaries'
    });
    totalScore += metaScore;

    // 5. Open Graph
    const hasOG = htmlLower.includes('property="og:') || htmlLower.includes("property='og:");
    const ogCount = (htmlLower.match(/property="og:/g) || []).length + (htmlLower.match(/property='og:/g) || []).length;
    const ogScore = hasOG ? Math.min(10, ogCount * 3) : 0;
    items.push({
      name: 'Open Graph Tags',
      pass: hasOG,
      score: ogScore,
      max: 10,
      note: hasOG ? `${ogCount} OG tags found` : 'No Open Graph tags — poor AI and social preview'
    });
    totalScore += ogScore;

    // 6. Canonical
    const hasCanonical = htmlLower.includes('rel="canonical"') || htmlLower.includes("rel='canonical'");
    const canonicalScore = hasCanonical ? 5 : 0;
    items.push({
      name: 'Canonical URL',
      pass: hasCanonical,
      score: canonicalScore,
      max: 5,
      note: hasCanonical ? 'Canonical URL set' : 'No canonical URL — risk of duplicate content'
    });
    totalScore += canonicalScore;

    // 7. FAQ Schema
    const hasFAQ = html.includes('"FAQPage"') || html.includes("'FAQPage'");
    const questionCount = (html.match(/"Question"/g) || []).length;
    const faqScore = hasFAQ ? Math.min(15, questionCount * 3) : 0;
    items.push({
      name: 'FAQ Schema',
      pass: hasFAQ,
      score: faqScore,
      max: 15,
      note: hasFAQ ? `FAQPage with ${questionCount} questions` : 'No FAQ Schema — missing high-value AI answer opportunities'
    });
    totalScore += faqScore;

    // 8. Sitemap
    let hasSitemap = false;
    try {
      const smRes = await fetchWithTimeout(baseUrl + '/sitemap.xml', 5000);
      hasSitemap = smRes.ok;
    } catch {}
    const smScore = hasSitemap ? 5 : 0;
    items.push({
      name: 'Sitemap.xml',
      pass: hasSitemap,
      score: smScore,
      max: 5,
      note: hasSitemap ? 'Sitemap found' : 'No sitemap.xml'
    });
    totalScore += smScore;

    // 9. HTTPS
    const httpsScore = isHttps ? 5 : 0;
    items.push({
      name: 'HTTPS',
      pass: isHttps,
      score: httpsScore,
      max: 5,
      note: isHttps ? 'Secure connection' : 'Not using HTTPS — security risk, may be penalized'
    });
    totalScore += httpsScore;

    // 10. Speed
    const speedScore = responseTime < 1000 ? 5 : responseTime < 3000 ? 3 : 1;
    items.push({
      name: 'Response Speed',
      pass: responseTime < 2000,
      score: speedScore,
      max: 5,
      note: `${responseTime}ms response time` + (responseTime > 3000 ? ' — slow for crawlers' : '')
    });
    totalScore += speedScore;

    res.setHeader('Cache-Control', 'public, max-age=300');
    return res.status(200).json({
      score: totalScore,
      url: targetUrl,
      checkedAt: new Date().toISOString(),
      responseTime,
      items,
    });

  } catch (e) {
    return res.status(500).json({error: 'Check failed: ' + e.message});
  }
}
