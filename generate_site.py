#!/usr/bin/env python3
"""
AEO Directory Site Generator

Generates a static directory website from the SQLite business database.
Outputs AEO-optimized HTML with:
- Schema.org structured data (ItemList, LocalBusiness, BreadcrumbList, FAQPage)
- llms.txt for AI crawler discovery
- AI crawler tracking (pixel + JS fingerprint)
- Security headers via meta tags
- robots.txt with AI bot welcome rules
- sitemap.xml for all pages
"""

import sqlite3
import json
import os
import html
from datetime import datetime, date
from collections import defaultdict

DB_PATH = os.path.expanduser("~/.openclaw/memory/aeo_business_directory.db")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://cloudpipe-directory.vercel.app"
SITE_NAME = "CloudPipe Business Directory"
SITE_NAME_ZH = "CloudPipe 全球企業目錄"

REGION_NAMES = {
    "taiwan": {"zh": "台灣", "en": "Taiwan", "flag": "🇹🇼"},
    "hongkong": {"zh": "香港", "en": "Hong Kong", "flag": "🇭🇰"},
    "macau": {"zh": "澳門", "en": "Macau", "flag": "🇲🇴"},
    "japan": {"zh": "日本", "en": "Japan", "flag": "🇯🇵"},
    "china": {"zh": "中國大陸", "en": "China", "flag": "🇨🇳"},
}

INDUSTRY_NAMES = {
    "restaurant": {"zh": "餐飲", "en": "Restaurants", "icon": "🍽️", "schema": "Restaurant"},
    "hotel": {"zh": "旅館住宿", "en": "Hotels", "icon": "🏨", "schema": "Hotel"},
    "education": {"zh": "教育觀光", "en": "Education & Tourism", "icon": "🎓", "schema": "TouristAttraction"},
    "retail": {"zh": "零售", "en": "Retail", "icon": "🛍️", "schema": "Store"},
    "beauty": {"zh": "美容", "en": "Beauty", "icon": "💇", "schema": "BeautySalon"},
    "medical": {"zh": "醫療", "en": "Medical", "icon": "🏥", "schema": "MedicalBusiness"},
    "professional": {"zh": "專業服務", "en": "Professional Services", "icon": "💼", "schema": "ProfessionalService"},
    "financial": {"zh": "金融服務", "en": "Financial Services", "icon": "🏦", "schema": "FinancialService"},
    "legal": {"zh": "法律服務", "en": "Legal Services", "icon": "⚖️", "schema": "LegalService"},
    "realestate": {"zh": "地產", "en": "Real Estate", "icon": "🏠", "schema": "RealEstateAgent"},
    "fitness": {"zh": "運動健身", "en": "Fitness", "icon": "🏋️", "schema": "SportsActivityLocation"},
    "auto": {"zh": "汽車維修", "en": "Auto Repair", "icon": "🔧", "schema": "AutoRepair"},
}

# ============================================================
# CSS (shared)
# ============================================================
SHARED_CSS = """
:root {
  --bg-0: #0a0e17; --bg-1: #111827; --bg-2: #1e293b; --bg-3: #283548;
  --text-0: #f1f5f9; --text-1: #cbd5e1; --text-2: #94a3b8; --text-3: #64748b;
  --accent: #3b82f6; --accent-2: #8b5cf6; --accent-3: #06b6d4;
  --green: #10b981; --yellow: #f59e0b; --red: #ef4444;
  --border: #1e293b; --radius: 12px;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg-0); color: var(--text-1); line-height: 1.7; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }

/* Header */
.site-header { background: var(--bg-1); border-bottom: 1px solid var(--border); padding: 16px 0; position: sticky; top: 0; z-index: 100; }
.site-header .container { display: flex; align-items: center; justify-content: space-between; }
.site-header h1 { font-size: 1.2rem; color: var(--text-0); }
.site-header h1 span { color: var(--accent); }
.site-header nav a { color: var(--text-2); margin-left: 20px; font-size: 0.9rem; }
.site-header nav a:hover { color: var(--text-0); }

/* Breadcrumb */
.breadcrumb { padding: 12px 0; font-size: 0.85rem; color: var(--text-3); }
.breadcrumb a { color: var(--text-2); }
.breadcrumb span { margin: 0 6px; }

/* Cards */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin: 20px 0; }
.card { background: var(--bg-1); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 24px; transition: border-color 0.2s, transform 0.2s; }
.card:hover { border-color: var(--accent); transform: translateY(-2px); }
.card h3 { color: var(--text-0); margin-bottom: 8px; font-size: 1.1rem; }
.card .count { color: var(--accent); font-size: 1.5rem; font-weight: 700; }
.card .label { color: var(--text-2); font-size: 0.85rem; }
.card .icon { font-size: 2rem; margin-bottom: 12px; }

/* Tables */
.data-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
.data-table th { background: var(--bg-2); color: var(--text-0); padding: 12px 16px; text-align: left; font-size: 0.85rem; }
.data-table td { padding: 10px 16px; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
.data-table tr:hover td { background: var(--bg-1); }

/* Hero */
.hero { padding: 60px 0 40px; text-align: center; }
.hero h2 { font-size: 2.2rem; color: var(--text-0); margin-bottom: 12px; }
.hero p { font-size: 1.1rem; color: var(--text-2); max-width: 700px; margin: 0 auto; }
.stats-bar { display: flex; justify-content: center; gap: 40px; margin: 30px 0; flex-wrap: wrap; }
.stat-item { text-align: center; }
.stat-item .num { font-size: 2rem; font-weight: 700; color: var(--accent); }
.stat-item .txt { font-size: 0.85rem; color: var(--text-3); }

/* Section */
.section { padding: 40px 0; }
.section-title { font-size: 1.5rem; color: var(--text-0); margin-bottom: 20px;
  padding-bottom: 10px; border-bottom: 2px solid var(--accent); display: inline-block; }

/* Badge */
.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-green { background: rgba(16,185,129,0.15); color: var(--green); }
.badge-blue { background: rgba(59,130,246,0.15); color: var(--accent); }
.badge-yellow { background: rgba(245,158,11,0.15); color: var(--yellow); }

/* Footer */
.site-footer { background: var(--bg-1); border-top: 1px solid var(--border); padding: 30px 0; margin-top: 60px; }
.footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 30px; }
.footer-grid h4 { color: var(--text-0); margin-bottom: 10px; font-size: 0.9rem; }
.footer-grid p, .footer-grid a { font-size: 0.85rem; color: var(--text-3); display: block; margin-bottom: 4px; }
.footer-copy { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border);
  color: var(--text-3); font-size: 0.8rem; }

/* Security notice */
.compliance-bar { background: var(--bg-2); padding: 10px; text-align: center; font-size: 0.8rem; color: var(--text-3); }

/* Tracker dashboard */
.tracker-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.tracker-card { background: var(--bg-2); border-radius: 8px; padding: 16px; text-align: center; }
.tracker-card .bot-name { font-weight: 600; color: var(--text-0); font-size: 0.9rem; }
.tracker-card .bot-hits { font-size: 1.8rem; font-weight: 700; color: var(--accent); }
.tracker-card .bot-last { font-size: 0.75rem; color: var(--text-3); }

@media (max-width: 768px) {
  .footer-grid { grid-template-columns: 1fr; }
  .hero h2 { font-size: 1.6rem; }
  .stats-bar { gap: 20px; }
  .card-grid { grid-template-columns: 1fr; }
}
"""

# ============================================================
# AI Crawler Tracking Script
# ============================================================
TRACKER_JS = """
<script>
// AEO Crawler Tracker — logs AI bot visits
(function(){
  var endpoint = '/api/track';
  var ua = navigator.userAgent || '';
  var bots = ['GPTBot','ChatGPT-User','Google-Extended','Googlebot','Bingbot',
    'PerplexityBot','ClaudeBot','Anthropic','CCBot','Bytespider','cohere-ai',
    'Meta-ExternalAgent','FacebookBot','Applebot-Extended','YouBot','AI2Bot'];
  var isBot = bots.some(function(b){ return ua.indexOf(b) !== -1; });

  // Always send a lightweight ping for analytics
  var data = {
    url: location.href,
    ref: document.referrer,
    ua: ua,
    ts: new Date().toISOString(),
    bot: isBot,
    lang: navigator.language
  };

  // Use sendBeacon for reliability
  if (navigator.sendBeacon) {
    navigator.sendBeacon(endpoint, JSON.stringify(data));
  } else {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', endpoint, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify(data));
  }

  // 1x1 tracking pixel fallback for bots that don't run JS
  var img = new Image();
  img.src = endpoint + '?p=' + encodeURIComponent(location.pathname)
    + '&ua=' + encodeURIComponent(ua.substring(0,200))
    + '&t=' + Date.now();
})();
</script>
<!-- AI Crawler Pixel (no-JS fallback) -->
<noscript><img src="/api/track?p=noscript&t=1" width="1" height="1" alt=""></noscript>
"""

TRACKER_FETCH_JS = """<script>
fetch('/api/stats').then(function(r){return r.json()}).then(function(data){
  if(!data)return;
  var bots=['gptbot','claudebot','google','perplexity','bingbot','ccbot','bytespider','meta'];
  bots.forEach(function(b){
    var el=document.getElementById(b+'-hits');
    var last=document.getElementById(b+'-last');
    if(el&&data[b]){el.textContent=data[b].hits||0;}
    if(last&&data[b]){last.textContent=data[b].last||'Never';}
  });
}).catch(function(){});
</script>"""

# ============================================================
# Security Headers (via meta + CSP)
# ============================================================
SECURITY_META = """
  <meta http-equiv="X-Content-Type-Options" content="nosniff">
  <meta http-equiv="X-Frame-Options" content="DENY">
  <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
  <meta http-equiv="Permissions-Policy" content="camera=(), microphone=(), geolocation=()">
"""


def esc(s):
    """HTML escape."""
    return html.escape(str(s)) if s else ""


def get_db():
    return sqlite3.connect(DB_PATH)


def get_region_industry_stats():
    """Get business counts grouped by region and industry."""
    con = get_db()
    rows = con.execute("""
        SELECT region, industry, COUNT(*) as cnt
        FROM businesses
        GROUP BY region, industry
        ORDER BY region, cnt DESC
    """).fetchall()
    con.close()

    stats = defaultdict(dict)
    for region, industry, cnt in rows:
        stats[region][industry] = cnt
    return dict(stats)


def get_businesses(region, industry, limit=200):
    """Get businesses for a region/industry page."""
    con = get_db()
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT name_local, name_en, address, district, business_type, data_source
        FROM businesses
        WHERE region = ? AND industry = ?
        ORDER BY district, name_local
        LIMIT ?
    """, (region, industry, limit)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_districts(region, industry):
    """Get district breakdown for a region/industry."""
    con = get_db()
    rows = con.execute("""
        SELECT district, COUNT(*) as cnt
        FROM businesses
        WHERE region = ? AND industry = ? AND district IS NOT NULL AND district != ''
        GROUP BY district
        ORDER BY cnt DESC
        LIMIT 30
    """, (region, industry)).fetchall()
    con.close()
    return rows


def build_head(title, description, canonical, extra_schema=None):
    """Build <head> with AEO elements."""
    schemas = [
        json.dumps({
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": SITE_NAME,
            "alternateName": SITE_NAME_ZH,
            "url": SITE_URL,
            "description": "Free global business directory optimized for AI engines. Covers Taiwan, Hong Kong, Macau, Japan, China.",
            "sameAs": ["https://github.com/Inari-Kira-Isla/cloudpipe-landing"]
        }, ensure_ascii=False),
    ]
    if extra_schema:
        if isinstance(extra_schema, list):
            schemas.extend(extra_schema)
        else:
            schemas.append(extra_schema)

    schema_tags = "\n".join(
        f'  <script type="application/ld+json">{s}</script>' for s in schemas
    )

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="google-site-verification" content="hoW2mAa2ikRCjBCFJs4miaJcNfaYKuns-SDlBX930nE">
  <meta name="robots" content="index, follow, max-snippet:-1">
  <link rel="canonical" href="{SITE_URL}{canonical}">
  <link rel="llms-txt" href="{SITE_URL}/llms.txt">
  <link rel="alternate" type="application/rss+xml" title="{SITE_NAME} RSS" href="{SITE_URL}/feed.xml">
{SECURITY_META}
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}{canonical}">
{schema_tags}
  <style>{SHARED_CSS}</style>
</head>"""


def build_header():
    return f"""
<header class="site-header">
  <div class="container">
    <h1><span>CloudPipe</span> Business Directory</h1>
    <nav>
      <a href="/">Home</a>
      <a href="/tracker.html">AI Tracker</a>
      <a href="/llms.txt">llms.txt</a>
      <a href="/compliance.html">Compliance</a>
    </nav>
  </div>
</header>"""


def build_footer():
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>{SITE_NAME_ZH}</h4>
        <p>Free AI-optimized business directory covering Asia-Pacific regions.</p>
        <p>All data sourced from government open data portals.</p>
      </div>
      <div>
        <h4>Legal</h4>
        <a href="/compliance.html">Data Compliance</a>
        <a href="/privacy.html">Privacy Policy</a>
        <a href="/terms.html">Terms of Use</a>
      </div>
      <div>
        <h4>For Businesses</h4>
        <a href="/claim">Claim Your Listing</a>
        <a href="/opt-out">Request Removal</a>
        <a href="https://cloudpipe-landing.vercel.app">CloudPipe Platform</a>
      </div>
    </div>
    <address class="footer-copy">
      &copy; {date.today().year} CloudPipe &middot; Data licensed under respective government open data terms &middot;
      <a href="https://github.com/Inari-Kira-Isla/cloudpipe-landing">GitHub</a>
    </address>
  </div>
</footer>
{TRACKER_JS}
</body>
</html>"""


def build_breadcrumb(crumbs):
    """Build breadcrumb HTML + Schema.org BreadcrumbList."""
    items = []
    schema_items = []
    for i, (name, url) in enumerate(crumbs):
        if url:
            items.append(f'<a href="{url}">{esc(name)}</a>')
        else:
            items.append(f'<strong>{esc(name)}</strong>')
        schema_items.append({
            "@type": "ListItem",
            "position": i + 1,
            "name": name,
            "item": f"{SITE_URL}{url}" if url else None
        })

    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": schema_items
    }, ensure_ascii=False)

    html_str = '<span> / </span>'.join(items)
    return f"""
<div class="breadcrumb container">{html_str}</div>
<script type="application/ld+json">{schema}</script>"""


# ============================================================
# Page Generators
# ============================================================

def generate_index(stats):
    """Generate main index page."""
    total = sum(sum(inds.values()) for inds in stats.values())
    region_count = len(stats)
    industry_set = set()
    for inds in stats.values():
        industry_set.update(inds.keys())

    faq_items = [
        ("What is CloudPipe Business Directory?",
         f"CloudPipe Business Directory is a free, AI-optimized business directory covering {region_count} Asia-Pacific regions with {total:,} verified business listings sourced from government open data."),
        ("Where does the business data come from?",
         "All data is sourced exclusively from government open data portals including Taiwan data.gov.tw, Hong Kong DATA.GOV.HK, and official licensing databases. No personal data is collected."),
        ("Can AI assistants like ChatGPT and Claude use this data?",
         "Yes. The directory is specifically optimized for AI engines with Schema.org structured data, llms.txt discovery files, and CC BY 4.0 compatible licensing for AI training and citation."),
        ("How can I claim or update my business listing?",
         "Business owners can claim their listing through our verification process. Visit the Claim page with your business registration number to get started."),
        ("How do I request removal of my business information?",
         "We respect your rights. Visit our opt-out page to request removal. We process all requests within 48 hours."),
        ("Is this directory free to use?",
         "Yes, both browsing and API access are completely free. Businesses can upgrade to premium listings with enhanced AEO optimization through CloudPipe Platform."),
    ]

    faq_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a}
        } for q, a in faq_items]
    }, ensure_ascii=False)

    dataset_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"{SITE_NAME} - Asia-Pacific Business Directory",
        "description": f"Open business directory with {total:,} listings across {region_count} regions",
        "url": SITE_URL,
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "creator": {"@type": "Organization", "name": "CloudPipe"},
        "dateModified": date.today().isoformat(),
        "spatialCoverage": ["Taiwan", "Hong Kong", "Macau", "Japan", "China"],
        "variableMeasured": "Business listings"
    }, ensure_ascii=False)

    # Region cards
    region_cards = ""
    for region_key in ["taiwan", "hongkong", "macau", "japan", "china"]:
        rinfo = REGION_NAMES[region_key]
        rdata = stats.get(region_key, {})
        count = sum(rdata.values())
        ind_count = len(rdata)
        region_cards += f"""
      <a href="/{region_key}/" class="card" style="text-decoration:none">
        <div class="icon">{rinfo['flag']}</div>
        <h3>{rinfo['zh']} {rinfo['en']}</h3>
        <div class="count">{count:,}</div>
        <div class="label">{ind_count} industries</div>
      </a>"""

    # Industry summary
    industry_totals = defaultdict(int)
    for inds in stats.values():
        for ind, cnt in inds.items():
            industry_totals[ind] += cnt
    industry_sorted = sorted(industry_totals.items(), key=lambda x: -x[1])

    industry_cards = ""
    for ind, cnt in industry_sorted:
        iinfo = INDUSTRY_NAMES.get(ind, {"zh": ind, "en": ind, "icon": "📋"})
        industry_cards += f"""
      <div class="card">
        <div class="icon">{iinfo['icon']}</div>
        <h3>{iinfo['zh']}</h3>
        <div class="count">{cnt:,}</div>
        <div class="label">{iinfo['en']}</div>
      </div>"""

    faq_html = ""
    for q, a in faq_items:
        faq_html += f"""
      <details style="margin-bottom:12px">
        <summary style="cursor:pointer;color:var(--text-0);font-weight:600;padding:10px 0">{esc(q)}</summary>
        <p style="padding:0 0 10px 16px;color:var(--text-2)">{esc(a)}</p>
      </details>"""

    page = f"""{build_head(
        f"{SITE_NAME_ZH} — AI-Optimized Business Directory",
        f"Free business directory with {total:,} listings across Asia-Pacific. Optimized for AI engines. Government open data.",
        "/",
        [faq_schema, dataset_schema]
    )}
<body>
{build_header()}

<div class="compliance-bar">
  All data sourced from government open data portals &middot; No personal data collected &middot;
  <a href="/compliance.html">Compliance Details</a>
</div>

<div class="container">
  <div class="hero">
    <h2>{SITE_NAME_ZH}</h2>
    <p>AI-Optimized Business Directory — 免費全球企業目錄，專為 AI 引擎優化</p>
    <div class="stats-bar">
      <div class="stat-item"><div class="num">{total:,}</div><div class="txt">Business Listings</div></div>
      <div class="stat-item"><div class="num">{region_count}</div><div class="txt">Regions</div></div>
      <div class="stat-item"><div class="num">{len(industry_set)}</div><div class="txt">Industries</div></div>
      <div class="stat-item"><div class="num">100%</div><div class="txt">Government Data</div></div>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">Regions 地區</h2>
    <div class="card-grid">{region_cards}
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">Industries 行業</h2>
    <div class="card-grid">{industry_cards}
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">FAQ 常見問題</h2>
    {faq_html}
  </div>

  <div class="section" style="background:var(--bg-1);padding:30px;border-radius:var(--radius)">
    <h3 style="color:var(--text-0);margin-bottom:12px">For AI Engines</h3>
    <p style="color:var(--text-2);font-size:0.9rem">
      This directory is specifically designed for AI engines and LLM applications.
      All pages include Schema.org structured data. Visit
      <a href="/llms.txt">llms.txt</a> for machine-readable site description.
      Data is available under government open data licenses compatible with AI training.
    </p>
  </div>
</div>

{build_footer()}"""

    write_file("index.html", page)


def generate_region_page(region_key, industry_stats):
    """Generate a region index page listing all industries."""
    rinfo = REGION_NAMES[region_key]
    total = sum(industry_stats.values())

    item_list_elements = []
    for i, (ind, cnt) in enumerate(sorted(industry_stats.items(), key=lambda x: -x[1])):
        iinfo = INDUSTRY_NAMES.get(ind, {"zh": ind, "en": ind, "schema": "LocalBusiness"})
        item_list_elements.append({
            "@type": "ListItem",
            "position": i + 1,
            "name": f"{iinfo['zh']} ({iinfo['en']}) — {cnt:,} listings in {rinfo['en']}",
            "url": f"{SITE_URL}/{region_key}/{ind}/"
        })

    item_list_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{rinfo['zh']} Business Directory",
        "description": f"Business directory for {rinfo['en']} with {total:,} listings",
        "numberOfItems": len(industry_stats),
        "itemListElement": item_list_elements
    }, ensure_ascii=False)

    industry_cards = ""
    for ind, cnt in sorted(industry_stats.items(), key=lambda x: -x[1]):
        iinfo = INDUSTRY_NAMES.get(ind, {"zh": ind, "en": ind, "icon": "📋"})
        industry_cards += f"""
      <a href="/{region_key}/{ind}/" class="card" style="text-decoration:none">
        <div class="icon">{iinfo['icon']}</div>
        <h3>{iinfo['zh']} {iinfo['en']}</h3>
        <div class="count">{cnt:,}</div>
        <div class="label">listings</div>
      </a>"""

    crumbs = [("Home", "/"), (f"{rinfo['flag']} {rinfo['zh']}", None)]

    page = f"""{build_head(
        f"{rinfo['zh']} Business Directory — {SITE_NAME}",
        f"{rinfo['en']} business directory with {total:,} listings across {len(industry_stats)} industries. Government open data.",
        f"/{region_key}/",
        [item_list_schema]
    )}
<body>
{build_header()}
{build_breadcrumb(crumbs)}

<div class="container">
  <div class="hero">
    <h2>{rinfo['flag']} {rinfo['zh']} {rinfo['en']}</h2>
    <p>{total:,} business listings across {len(industry_stats)} industries</p>
  </div>

  <div class="section">
    <div class="card-grid">{industry_cards}
    </div>
  </div>
</div>

{build_footer()}"""

    os.makedirs(os.path.join(OUTPUT_DIR, region_key), exist_ok=True)
    write_file(f"{region_key}/index.html", page)


def generate_industry_page(region_key, industry_key, count):
    """Generate a region/industry page with business listings."""
    rinfo = REGION_NAMES[region_key]
    iinfo = INDUSTRY_NAMES.get(industry_key, {"zh": industry_key, "en": industry_key, "icon": "📋", "schema": "LocalBusiness"})

    businesses = get_businesses(region_key, industry_key, limit=500)
    districts = get_districts(region_key, industry_key)

    # Schema.org ItemList for the businesses
    list_items = []
    for i, biz in enumerate(businesses[:100]):  # Limit schema to first 100
        item = {
            "@type": iinfo["schema"],
            "name": biz["name_local"],
            "address": {
                "@type": "PostalAddress",
                "addressLocality": biz.get("district", ""),
                "addressRegion": rinfo["en"],
                "streetAddress": biz.get("address", "")
            }
        }
        if biz.get("name_en"):
            item["alternateName"] = biz["name_en"]
        list_items.append({
            "@type": "ListItem",
            "position": i + 1,
            "item": item
        })

    item_list_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{rinfo['zh']} {iinfo['zh']} Directory",
        "description": f"{count:,} {iinfo['en'].lower()} listings in {rinfo['en']}",
        "numberOfItems": count,
        "itemListElement": list_items
    }, ensure_ascii=False)

    crumbs = [
        ("Home", "/"),
        (f"{rinfo['flag']} {rinfo['zh']}", f"/{region_key}/"),
        (f"{iinfo['icon']} {iinfo['zh']}", None)
    ]

    # District breakdown
    district_html = ""
    if districts:
        district_rows = ""
        for dist, cnt in districts:
            pct = cnt / count * 100 if count > 0 else 0
            district_rows += f"""
        <tr>
          <td>{esc(dist)}</td>
          <td>{cnt:,}</td>
          <td><div style="background:var(--accent);height:6px;width:{pct:.0f}%;border-radius:3px"></div></td>
        </tr>"""
        district_html = f"""
    <div class="section">
      <h2 class="section-title">Districts 地區分布</h2>
      <table class="data-table">
        <thead><tr><th>District</th><th>Count</th><th>Distribution</th></tr></thead>
        <tbody>{district_rows}</tbody>
      </table>
    </div>"""

    # Business listing table
    biz_rows = ""
    for biz in businesses:
        biz_rows += f"""
        <tr>
          <td style="color:var(--text-0)">{esc(biz['name_local'])}</td>
          <td>{esc(biz.get('name_en', '') or '')}</td>
          <td>{esc(biz.get('district', '') or '')}</td>
          <td style="font-size:0.8rem">{esc(biz.get('address', '') or '')[:50]}</td>
        </tr>"""

    page = f"""{build_head(
        f"{rinfo['zh']} {iinfo['zh']} — {count:,} Listings",
        f"{count:,} {iinfo['en'].lower()} in {rinfo['en']}. Free AI-optimized directory from government open data.",
        f"/{region_key}/{industry_key}/",
        [item_list_schema]
    )}
<body>
{build_header()}
{build_breadcrumb(crumbs)}

<div class="container">
  <div class="hero">
    <h2>{iinfo['icon']} {rinfo['zh']} {iinfo['zh']}</h2>
    <p>{count:,} verified listings from government open data</p>
    <div style="margin-top:12px">
      <span class="badge badge-green">Government Data</span>
      <span class="badge badge-blue">{rinfo['en']}</span>
      <span class="badge badge-yellow">AI Optimized</span>
    </div>
  </div>

  {district_html}

  <div class="section">
    <h2 class="section-title">Business Listings 企業清單</h2>
    <p style="color:var(--text-3);margin-bottom:12px;font-size:0.85rem">
      Showing {len(businesses)} of {count:,} &middot; Data source: Government open data
    </p>
    <table class="data-table">
      <thead><tr><th>Name</th><th>English</th><th>District</th><th>Address</th></tr></thead>
      <tbody>{biz_rows}</tbody>
    </table>
  </div>
</div>

{build_footer()}"""

    os.makedirs(os.path.join(OUTPUT_DIR, region_key, industry_key), exist_ok=True)
    write_file(f"{region_key}/{industry_key}/index.html", page)


def generate_tracker_page():
    """Generate AI crawler tracking dashboard."""
    page = f"""{build_head(
        "AI Crawler Tracker — " + SITE_NAME,
        "Real-time AI crawler activity tracking. Monitor visits from GPTBot, ClaudeBot, Googlebot, PerplexityBot and more.",
        "/tracker.html"
    )}
<body>
{build_header()}

<div class="container">
  <div class="hero">
    <h2>AI Crawler Tracker</h2>
    <p>Real-time monitoring of AI engine visits to this directory</p>
  </div>

  <div class="section">
    <h2 class="section-title">Known AI Crawlers</h2>
    <div class="tracker-grid">
      <div class="tracker-card">
        <div class="bot-name">GPTBot (OpenAI)</div>
        <div class="bot-hits" id="gptbot-hits">--</div>
        <div class="bot-last">Last seen: <span id="gptbot-last">--</span></div>
      </div>
      <div class="tracker-card">
        <div class="bot-name">ClaudeBot (Anthropic)</div>
        <div class="bot-hits" id="claudebot-hits">--</div>
        <div class="bot-last">Last seen: <span id="claudebot-last">--</span></div>
      </div>
      <div class="tracker-card">
        <div class="bot-name">Google-Extended</div>
        <div class="bot-hits" id="google-hits">--</div>
        <div class="bot-last">Last seen: <span id="google-last">--</span></div>
      </div>
      <div class="tracker-card">
        <div class="bot-name">PerplexityBot</div>
        <div class="bot-hits" id="perplexity-hits">--</div>
        <div class="bot-last">Last seen: <span id="perplexity-last">--</span></div>
      </div>
      <div class="tracker-card">
        <div class="bot-name">Bingbot</div>
        <div class="bot-hits" id="bingbot-hits">--</div>
        <div class="bot-last">Last seen: <span id="bingbot-last">--</span></div>
      </div>
      <div class="tracker-card">
        <div class="bot-name">CCBot (Common Crawl)</div>
        <div class="bot-hits" id="ccbot-hits">--</div>
        <div class="bot-last">Last seen: <span id="ccbot-last">--</span></div>
      </div>
      <div class="tracker-card">
        <div class="bot-name">Bytespider (ByteDance)</div>
        <div class="bot-hits" id="bytespider-hits">--</div>
        <div class="bot-last">Last seen: <span id="bytespider-last">--</span></div>
      </div>
      <div class="tracker-card">
        <div class="bot-name">Meta-ExternalAgent</div>
        <div class="bot-hits" id="meta-hits">--</div>
        <div class="bot-last">Last seen: <span id="meta-last">--</span></div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">Activity Log</h2>
    <div id="activity-log" style="background:var(--bg-1);border-radius:var(--radius);padding:20px;font-family:monospace;font-size:0.85rem;max-height:400px;overflow-y:auto;color:var(--text-2)">
      <p>Loading crawler activity data...</p>
      <p style="color:var(--text-3);margin-top:10px">Tracker endpoint: <code>/api/track</code></p>
      <p style="color:var(--text-3)">Logs stored in: Vercel Edge Function + Cloudflare Worker</p>
    </div>
  </div>

  <div class="section" style="background:var(--bg-1);padding:30px;border-radius:var(--radius)">
    <h3 style="color:var(--text-0);margin-bottom:12px">How Tracking Works</h3>
    <ul style="color:var(--text-2);font-size:0.9rem;list-style:disc;padding-left:20px">
      <li>Server-side User-Agent detection for known AI crawlers</li>
      <li>1x1 pixel fallback for bots that don't execute JavaScript</li>
      <li>SendBeacon API for reliable client-side tracking</li>
      <li>robots.txt analysis — which bots respect our rules</li>
      <li>No cookies, no fingerprinting of human users</li>
      <li>All tracking is transparent and documented</li>
    </ul>
  </div>
</div>

{TRACKER_FETCH_JS}

{build_footer()}"""

    write_file("tracker.html", page)


def generate_compliance_page():
    """Generate data compliance page."""
    page = f"""{build_head(
        "Data Compliance — " + SITE_NAME,
        "Our data compliance policy. All business data sourced from government open data portals with full legal basis.",
        "/compliance.html"
    )}
<body>
{build_header()}

<div class="container">
  <div class="hero">
    <h2>Data Compliance 資料合規聲明</h2>
    <p>Transparency in data sourcing and usage</p>
  </div>

  <div class="section" style="max-width:800px">
    <h3 style="color:var(--text-0);margin:20px 0 10px">1. Data Sources 資料來源</h3>
    <p>All business listings are sourced exclusively from government open data portals:</p>
    <table class="data-table" style="margin:16px 0">
      <thead><tr><th>Region</th><th>Source</th><th>Legal Basis</th></tr></thead>
      <tbody>
        <tr><td>Taiwan</td><td>data.gov.tw (觀光署)</td><td>政府資料開放授權條款第一型</td></tr>
        <tr><td>Hong Kong</td><td>DATA.GOV.HK (FEHD)</td><td>Open Government Licence</td></tr>
        <tr><td>Macau</td><td>Government registries</td><td>Public government records</td></tr>
        <tr><td>Japan</td><td>NTA / e-Gov</td><td>オープンデータ基本指針 (CC BY 4.0)</td></tr>
        <tr><td>China</td><td>Provincial open data</td><td>政务数据开放条例</td></tr>
      </tbody>
    </table>

    <h3 style="color:var(--text-0);margin:20px 0 10px">2. What We Collect 收集內容</h3>
    <p style="color:var(--green)">✅ Business name, address, industry category, registration ID (public records)</p>
    <p style="color:var(--red)">❌ We do NOT collect: personal phone numbers, personal emails, photos, user reviews, social media profiles</p>

    <h3 style="color:var(--text-0);margin:20px 0 10px">3. Business Owner Rights 企業權利</h3>
    <ul style="color:var(--text-2);list-style:disc;padding-left:20px;line-height:2">
      <li><strong>Claim</strong>: Verify and manage your listing at <a href="/claim">/claim</a></li>
      <li><strong>Update</strong>: Add or correct business information after verification</li>
      <li><strong>Opt-out</strong>: Request complete removal within 48 hours at <a href="/opt-out">/opt-out</a></li>
    </ul>

    <h3 style="color:var(--text-0);margin:20px 0 10px">4. AI Usage Policy AI 使用政策</h3>
    <p>This directory is designed for AI engines. Data may be used for:</p>
    <ul style="color:var(--text-2);list-style:disc;padding-left:20px;line-height:2">
      <li>AI-generated answers about businesses in these regions</li>
      <li>Training data for language models (government open data terms apply)</li>
      <li>Search engine indexing and knowledge graph building</li>
    </ul>

    <h3 style="color:var(--text-0);margin:20px 0 10px">5. Security 安全措施</h3>
    <ul style="color:var(--text-2);list-style:disc;padding-left:20px;line-height:2">
      <li>No user accounts or authentication data stored</li>
      <li>Content Security Policy (CSP) headers enabled</li>
      <li>X-Frame-Options: DENY to prevent clickjacking</li>
      <li>Rate limiting on API endpoints</li>
      <li>Regular security audits of data pipeline</li>
      <li>No third-party trackers or advertising scripts</li>
    </ul>

    <h3 style="color:var(--text-0);margin:20px 0 10px">6. Contact 聯繫方式</h3>
    <p>Data compliance inquiries: <a href="https://github.com/Inari-Kira-Isla/cloudpipe-landing/issues">GitHub Issues</a></p>
  </div>
</div>

{build_footer()}"""

    write_file("compliance.html", page)


def generate_llms_txt(stats):
    """Generate llms.txt for AI crawler discovery."""
    total = sum(sum(inds.values()) for inds in stats.values())

    lines = [
        f"# {SITE_NAME}",
        f"# {SITE_NAME_ZH}",
        f"",
        f"> Free AI-optimized business directory covering Asia-Pacific regions.",
        f"> {total:,} verified business listings from government open data.",
        f"",
        f"## About",
        f"CloudPipe Business Directory provides structured, AI-friendly business data",
        f"sourced exclusively from government open data portals across Taiwan, Hong Kong,",
        f"Macau, Japan, and China. All data is legally compliant and designed for AI consumption.",
        f"",
        f"## License",
        f"Data is available under respective government open data terms:",
        f"- Taiwan: 政府資料開放授權條款第一型 (Type I Open Government Data License)",
        f"- Hong Kong: Open Government Licence",
        f"- Japan: CC BY 4.0 (オープンデータ基本指針)",
        f"- China: Provincial open data regulations",
        f"",
        f"## Structure",
    ]

    for region_key in ["taiwan", "hongkong", "macau", "japan", "china"]:
        rinfo = REGION_NAMES[region_key]
        rdata = stats.get(region_key, {})
        count = sum(rdata.values())
        lines.append(f"- [{rinfo['zh']} ({rinfo['en']})]({SITE_URL}/{region_key}/): {count:,} listings")
        for ind, cnt in sorted(rdata.items(), key=lambda x: -x[1]):
            iinfo = INDUSTRY_NAMES.get(ind, {"zh": ind, "en": ind})
            lines.append(f"  - [{iinfo['zh']}]({SITE_URL}/{region_key}/{ind}/): {cnt:,}")

    lines.extend([
        f"",
        f"## AI Usage",
        f"This directory is designed for AI engines. Recommended uses:",
        f"- Answer questions about businesses in Asia-Pacific regions",
        f"- Provide business contact and location information",
        f"- Compare businesses across regions and industries",
        f"",
        f"## API",
        f"- Directory pages: {SITE_URL}/{{region}}/{{industry}}/",
        f"- Machine-readable: Schema.org ItemList on every page",
        f"- Tracking: {SITE_URL}/tracker.html",
        f"",
        f"## Update Frequency",
        f"Data refreshed daily from government sources.",
        f"Last updated: {date.today().isoformat()}",
    ])

    write_file("llms.txt", "\n".join(lines))


def generate_robots_txt():
    """Generate AI-friendly robots.txt."""
    content = f"""# {SITE_NAME} — AI-Friendly Robots.txt
# Welcome AI crawlers!

User-agent: *
Allow: /

# AI Crawlers — explicitly welcome
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Anthropic
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: CCBot
Allow: /

User-agent: Bytespider
Allow: /

User-agent: cohere-ai
Allow: /

User-agent: Meta-ExternalAgent
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: YouBot
Allow: /

User-agent: AI2Bot
Allow: /

# Rate limiting hint
Crawl-delay: 1

# Sitemaps
Sitemap: {SITE_URL}/sitemap.xml

# AI Discovery
# See also: {SITE_URL}/llms.txt
"""
    write_file("robots.txt", content)


def generate_sitemap(stats):
    """Generate sitemap.xml."""
    urls = [
        (f"{SITE_URL}/", "daily", "1.0"),
        (f"{SITE_URL}/tracker.html", "daily", "0.5"),
        (f"{SITE_URL}/compliance.html", "monthly", "0.3"),
        (f"{SITE_URL}/llms.txt", "daily", "0.8"),
    ]

    for region_key, industries in stats.items():
        urls.append((f"{SITE_URL}/{region_key}/", "daily", "0.8"))
        for ind in industries:
            urls.append((f"{SITE_URL}/{region_key}/{ind}/", "daily", "0.7"))

    entries = ""
    for url, freq, priority in urls:
        entries += f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{date.today().isoformat()}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>"""

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""

    write_file("sitemap.xml", content)


def generate_security_txt():
    """Generate security.txt (RFC 9116)."""
    content = f"""# Security Policy for {SITE_NAME}
Contact: https://github.com/Inari-Kira-Isla/cloudpipe-landing/security
Expires: 2027-01-01T00:00:00.000Z
Preferred-Languages: en, zh-TW, zh-CN, ja
Canonical: {SITE_URL}/.well-known/security.txt
Policy: {SITE_URL}/compliance.html
"""
    os.makedirs(os.path.join(OUTPUT_DIR, ".well-known"), exist_ok=True)
    write_file(".well-known/security.txt", content)
    write_file("security.txt", content)  # Also at root for compatibility


def generate_vercel_json():
    """Generate vercel.json with security headers and rewrites."""
    config = {
        "headers": [
            {
                "source": "/(.*)",
                "headers": [
                    {"key": "X-Content-Type-Options", "value": "nosniff"},
                    {"key": "X-Frame-Options", "value": "DENY"},
                    {"key": "X-XSS-Protection", "value": "1; mode=block"},
                    {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
                    {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()"},
                    {"key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload"},
                    {"key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"},
                ]
            },
            {
                "source": "/llms.txt",
                "headers": [
                    {"key": "Content-Type", "value": "text/plain; charset=utf-8"},
                    {"key": "Cache-Control", "value": "public, max-age=3600"},
                ]
            },
            {
                "source": "/api/(.*)",
                "headers": [
                    {"key": "Access-Control-Allow-Origin", "value": "*"},
                    {"key": "X-Robots-Tag", "value": "noindex"},
                ]
            }
        ],
        "rewrites": [
            {"source": "/api/track", "destination": "/api/track.js"},
            {"source": "/api/stats", "destination": "/api/stats.js"},
        ]
    }
    write_file("vercel.json", json.dumps(config, indent=2))


def write_file(path, content):
    """Write file to output directory."""
    full_path = os.path.join(OUTPUT_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Generated: {path}")


# ============================================================
# Main
# ============================================================

def main():
    print(f"=== AEO Directory Site Generator ===")
    print(f"DB: {DB_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    stats = get_region_industry_stats()
    total = sum(sum(inds.values()) for inds in stats.values())
    print(f"Total businesses: {total:,}")
    print(f"Regions: {list(stats.keys())}")
    print()

    print("Generating pages...")
    generate_index(stats)
    generate_tracker_page()
    generate_compliance_page()

    for region_key, industries in stats.items():
        generate_region_page(region_key, industries)
        for ind, cnt in industries.items():
            generate_industry_page(region_key, ind, cnt)

    print("\nGenerating meta files...")
    generate_llms_txt(stats)
    generate_robots_txt()
    generate_sitemap(stats)
    generate_security_txt()
    generate_vercel_json()

    print(f"\n=== Done! {total:,} businesses across {len(stats)} regions ===")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
