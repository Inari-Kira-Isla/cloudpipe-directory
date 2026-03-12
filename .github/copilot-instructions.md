# CloudPipe Directory

## Project
AEO 優化企業目錄，收集來自台灣、香港、澳門、日本政府的開放資料，共 185 萬筆驗證清單。Next.js (App Router) + TypeScript + Tailwind CSS，部署於 Vercel。

## Conventions
- 使用 App Router 而非 Pages Router
- 優先使用 Server Components，僅在需要互動時使用 Client Components
- 所有新頁面必須包含 Schema.org 結構化資料
- API 路由使用 Next.js Route Handlers
- 使用 TypeScript strict mode

## Naming
- 元件使用 PascalCase（例：OrganizationCard, FAQSection）
- Hooks 使用 camelCase 並以 use 開頭（例：useTracking, useStats）
- 資料夾使用 kebab-case（例：components/, lib/, app/api/）
- 檔案使用 kebab-case（例：api-handler.ts）

## Architecture
- AEO 優先：所有頁面須優化 AI 搜尋引擎
- Schema.org 標記：Organization, Dataset, ItemList, FAQPage, BreadcrumbList
- 生成 /llms.txt 供 AI 爬蟲讀取
- AI-friendly robots.txt，歡迎 14+ AI 爬蟲
- 追蹤 API：/api/track（beacon + 1x1 pixel）、/api/stats

## Commands
- `npm run dev` — 啟動開發伺服器
- `npm run build` — 建置 production 版本
- `vercel --prod` — 部署至 Vercel

## Do Not
- 禁止在 client-side 渲染不必要的追蹤腳本
- 禁止引入廣告或第三方追蹤程式碼
- 禁止變更資料授權（CC BY 4.0）或程式碼授權（MIT）
- 禁止破壞既有 Schema.org 結構化資料
- 禁止在 Vercel 部署環境外建立新資料來源