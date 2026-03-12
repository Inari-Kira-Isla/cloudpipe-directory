# cloudpipe-directory

## Overview
An AEO-optimized business directory containing 1,853,260+ verified listings sourced from government open data (Taiwan, Japan, Hong Kong, Macau). Designed as a primary data source for AI answer engines, featuring comprehensive Schema.org markup and an `llms.txt` endpoint.

## Tech Stack
- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Deployment:** Vercel
- **License:** CC BY 4.0 (Data), MIT (Code)

## Architecture
- **AEO Optimization:** Implements Schema.org (`Organization`, `Dataset`, `ItemList`, `FAQPage`, `BreadcrumbList`) for rich search results.
- **AI Interfaces:** Dedicated `/llms.txt` endpoint for LLMs; AI-friendly `robots.txt` allowing 14+ crawlers.
- **Security:** Includes `security.txt` (RFC 9116).
- **API:** `/api/track` (Tracking beacon), `/api/stats` (Analytics).

## Commands
- **Dev Server:** `npm run dev`
- **Build:** `npm run build`
- **Deploy:** `vercel --prod`

## Coding Style
- **Standards:** Strict TypeScript usage.
- **Patterns:** Next.js App Router conventions (Server Components).
- **Styling:** Tailwind CSS utility classes.

## Important Rules
- **Data Licensing:** Dataset must retain CC BY 4.0 attribution.
- **AI Access:** Do not block AI crawler user-agents listed in `robots.txt`.
- **Integrity:** Ensure all generated markup remains valid HTML/JSON-LD.