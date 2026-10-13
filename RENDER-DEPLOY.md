# Render 部署設定

此套件是單管理員、單服務實例的網站與後台；不含本機資料庫或帳號。公開前需要設定下列環境變數。

- Runtime: Python 3
- Build command: python -c "print('No additional dependencies')"
- Start command: python server.py
- BREASTCARE_PRODUCTION=1
- BREASTCARE_STATE=/var/data/breastcare
- PUBLIC_ORIGIN=https://你的服務名稱.onrender.com （不得帶結尾斜線）
- ADMIN_INITIAL_PASSWORD：由管理員自行設定至少16字元；放在Render環境變數，不放GitHub。
- 永久磁碟掛載 /var/data，需付費服務。單實例運作。

管理員密碼在空資料庫首次啟動時建立；公開環境禁止任何人透過網頁自行初始化帳號。成功建立後，可移除 ADMIN_INITIAL_PASSWORD 環境變數。重啟後需重新登入。既有本機資料沒有自動匯入，若需遷移應另行安全傳輸資料庫。

本機預覽仍使用 python3 server.py，預設只監聽127.0.0.1。

操作紀錄保存於資料庫audit表。更新網站時勿替換永久磁碟資料庫。網站功能測試與HTTPS、登入、公開證書欄位均須在部署後再確認。

備份：在主機Shell執行 python backup.py；會將SQLite安全快照保存於資料目錄backups/，每天一份。備份須另行排程並定期保存在主機以外的安全位置。只有同一顆磁碟上的副本不足以取代外部備份。

課程付款與影片開通依舊透過LINE人工安排；沒有自動金流或影片權限系統。
