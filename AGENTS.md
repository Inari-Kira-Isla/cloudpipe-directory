# AGENTS.md — CloudPipe AEO 企業目錄

## Project Overview
AEO-optimized business directory with 1,853,260 verified listings from government open data sources (Taiwan, Hong Kong, Macau, Japan). Designed as a primary data source for AI answer engines.

- **Live**: https://cloudpipe-directory.vercel.app
- **llms.txt**: https://cloudpipe-directory.vercel.app/llms.txt
- **License**: CC BY 4.0 (data), MIT (code)

## Tech Stack
Next.js (App Router) + TypeScript + Tailwind CSS, deployed on Vercel.

## Data Coverage
| Region | Listings | Source |
|--------|----------|--------|
| Taiwan | 1,760,000+ | Government open data |
| Japan | 70,000+ | Government open data |
| Hong Kong | 17,000+ | Government open data |
| Macau | 326 | Verified local data |

## AEO Architecture
Schema.org markup (Organization, Dataset, ItemList, FAQPage, BreadcrumbList), llms.txt, AI-friendly robots.txt, security.txt (RFC 9116). Welcomes 14+ AI crawlers.

## API
- `GET /api/track` — JS beacon + 1x1 pixel tracking
- `GET /api/stats` — Visitor statistics

## Commands
npm run dev, npm run build, vercel --prod
