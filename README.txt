恩聚共行｜完整活動流程 v7

固定流程：
首頁（既有 live UI，不是 screenshot）
→ 我要報名
→ 第1頁 活動概覽（按鈕：了解詳情）
→ 第2頁 Tému Stay 場地介紹 + 12 張官方網站不同照片 + 活動意義
→ 第3頁 預算說明
→ 第4頁 報名表
→ 第5頁 報名成功
→ 第6頁 活動資訊 & FAQ

首頁留言：
- 「留言同行」區塊可直接輸入暱稱與留言，不需要 GitHub 帳號
- 暱稱最多 20 字元，留言最多 300 字元
- 前端由 GitHub Pages 提供
- 留言 API 部署在 Railway
- 留言永久儲存在 Railway PostgreSQL
- API：GET /api/comments、POST /api/comments
- 健康檢查：GET /health
- CORS 僅允許指定網站來源
- 具備基本 IP 頻率限制
- 前端以 textContent 顯示留言，不執行留言中的 HTML

本機執行：
  pip install -r requirements.txt
  設定 DATABASE_URL
  py server.py
開啟：
  http://127.0.0.1:5000

正式架構：
  GitHub Pages → Railway Flask API → Railway PostgreSQL

重要：
- Railway API 網址：https://acts-comments-api-production.up.railway.app
- PostgreSQL 為私有服務，沒有公開資料庫 domain。
- 不要將 DATABASE_URL 或其他資料庫密碼寫入前端或 GitHub。
- 程式沒有把任何六頁 screenshot、PDF 頁面或 screen capture 當作網頁。
- 首頁沿用之前已確認的 live HTML/CSS 與乾淨素材。
- Gallery 12 張全部是 Tému Stay 官方 Gallery 的不同圖片 URL，不再用同圖 crop。
- 因 Gallery 使用 Tému Stay 官方網站圖片，瀏覽第2頁時需要網路連線。
- Prototype 報名表目前不儲存姓名、電話等個資。
