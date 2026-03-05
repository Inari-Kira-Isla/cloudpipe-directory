# Google Search Console 設定指南

## 步驟 1：驗證網站擁有權（需在瀏覽器操作）

1. 打開 https://search.google.com/search-console
2. 點擊「新增資源」
3. 選擇「URL 前綴」，輸入：`https://cloudpipe-directory.vercel.app`
4. 選擇「HTML 標記」驗證方式
5. 複製 meta 標記內容（類似 `google-site-verification=XXXXXXX`）
6. 告訴 Claude 這個 verification code，我會自動加到所有頁面

## 步驟 2：提交 Sitemap

驗證成功後，在 Search Console 中：
1. 左側選單 → Sitemaps
2. 輸入：`sitemap.xml`
3. 點擊「提交」

也要提交：
- `https://cloudpipe-landing.vercel.app` (同樣步驟)

## 步驟 3：要求索引（可選）

在 URL 檢查工具中，逐一輸入重要頁面要求索引：
- `https://cloudpipe-directory.vercel.app/`
- `https://cloudpipe-directory.vercel.app/taiwan/`
- `https://cloudpipe-directory.vercel.app/hongkong/`
- `https://cloudpipe-directory.vercel.app/check.html`
