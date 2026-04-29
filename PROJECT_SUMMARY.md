# 台股分析工具箱 — 專案摘要（AI 閱讀版）

> 本文件為讓 Claude 或其他 AI 快速掌握專案全貌，供每次對話開始時作為上下文參考。

---

## 1. 專案概述

這是一個個人使用的**台股籌碼分析全端 Web App**，由一位無程式背景的使用者（Lisa）從零開始建立。靈感來自「M哥 ABC 選股框架」（趨勢 + 法人買超 + 量縮 + 信念持有），設計參考 籌碼K線 與 山竹股市 兩款 App。

**核心目標**：追蹤法人買賣超、計算外資成本、識別籌碼訊號、產生 AI 分析報告。

---

## 2. 架構與部署

| 層次 | 技術 | 部署位置 |
|------|------|----------|
| Backend | Python + FastAPI + Uvicorn | Railway（雲端） |
| Frontend | 純 HTML / JavaScript / Chart.js | GitHub Pages（`stock-frontend` repo） |

### Frontend 頁面清單
- `home.html` — 首頁入口
- `index.html` — 主工具（法人成本追蹤，含籌碼掃描功能）
- `ABC選股掃描.html` — ABC 框架掃描
- `籌碼分析.html` — 個股籌碼詳細分析
- `興櫃股票分析.html` — 興櫃市場分析
- `即時資金雷達Pro.html` — 即時資金流向與 Discord 推播監控

### 身份驗證
- 使用簡單 Header Token：`x-token`
- 後端讀取：`API_TOKEN = os.environ.get("API_TOKEN", "0921")`
- 前端將 Token 存入 `sessionStorage` 與 `localStorage`（跨分頁通用）

---

## 3. 後端 API 端點（`main.py`）

所有端點均需 Header `x-token`，否則回傳 401。

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/history/{symbol}` | 個股日K歷史（Fugle） |
| GET | `/ticker/{symbol}` | 個股即時報價（Fugle 盤中） |
| GET | `/foreign/{symbol}` | 外資買賣超（FinMind，2年） |
| GET | `/margin/{symbol}` | 融資餘額（FinMind，2年） |
| GET | `/price/{symbol}` | 個股收盤價（FinMind `TaiwanStockPrice`，2年） |
| GET | `/theme/{symbol}` | 股票主題分類 + 對應美股 |
| GET | `/us_price/{ticker}` | 美股近5日收盤（Yahoo Finance） |
| GET | `/news` | 權證新聞（Google News RSS → 經濟日報） |
| GET | `/revenue/{symbol}` | 月營收 + MoM/YoY（FinMind，2年） |
| GET | `/market_volume` | 大盤前100成交量（TWSE MI_INDEX20） |
| GET | `/industry_stocks/{industry}` | 產業/主題股票清單 |
| GET | `/emerging_analysis` | 興櫃股票篩選分析（TPEX） |
| POST | `/scan` | 個股外資成本快速掃描（最多10檔） |
| POST | `/technical_scan` | 技術面+外資成本全市場掃描 |
| POST | `/analyze` | AI 分析報告（Anthropic Claude API，30分鐘快取） |
| GET | `/chip_scan` | 指定股票清單的外資＋投信雙買超掃描 |
| GET | `/chips/{symbol}` | 個股籌碼摘要（前端籌碼分析主資料） |
| GET | `/flow/summary` | 即時資金雷達總覽（上市＋上櫃，3分鐘快取） |
| GET | `/flow/stock/{code}` | 單股資金流向＋近20日法人/金額時間軸 |
| GET | `/flow/industry/{name}` | 產業資金流向詳細 |
| GET | `/flow/status` | 即時資金雷達快取/狀態確認 |
| POST | `/flow/monitor` | 盤中 Discord 自動監控與推播 |
| POST | `/flow/test_discord` | Discord Webhook 測試訊息 |

---

## 4. 資料來源

| 來源 | 用途 | 注意事項 |
|------|------|---------|
| **FinMind API**（Backer 方案 NT$699/月） | 法人買賣超、股價、融資、月營收 | 主要資料骨幹；全市場查詢不需 `data_id` |
| **Fugle API** | 個股 K 線、即時報價 | 歷史資料使用還原價，**不適合**用於現價顯示 |
| **TWSE 端點** | 大盤成交量（MI_INDEX20、STOCK_DAY_ALL） | 在 Lisa 的網路環境**頻繁 timeout**，謹慎使用 |
| **TPEX** | 興櫃即時行情 | 交易時段才有資料 |
| **Yahoo Finance** | 美股近期收盤價 | 透過 `yfinance` 或直接 HTTP 抓取 |
| **Google News RSS** | 權證新聞 | 篩選 money.udn.com |
| **Anthropic Claude API** | 股票 AI 分析報告 | 使用 `claude-sonnet-4-20250514`，有 30 分鐘快取 |
| **TWSE MIS** | 即時資金雷達（盤中價量） | 作為 `/flow/*` 主資料來源，搭配 3 分鐘快取 |

---

## 5. 核心計算邏輯

### 外資成本計算
- 使用**收盤價**（非均價）計算外資持倉成本，最接近 籌碼K線 等參考 App
- 資料區間：2年歷史
- 演算法：
  ```
  for 每日外資異動:
      if 買超:
          total_cost += 買超張數 × 1000 × 當日收盤
          holdings  += 買超張數 × 1000
      if 賣超 and holdings > 0:
          sold = min(賣超張數 × 1000, holdings)
          total_cost -= sold × (total_cost / holdings)  # 加權平均攤銷
          holdings   -= sold
  f_cost = total_cost / holdings
  ```

### 波段密碼區間（外資成本 → 目標價）
| 區間 | 條件 | CSS 標籤 |
|------|------|----------|
| 跌破成本 | close < f_cost | neutral |
| 醞釀期 | f_cost ≤ close < f_cost × 1.04 | neutral |
| 第一攻擊區 | f_cost × 1.04 ≤ close < f_cost × 1.2 | good |
| 第二攻擊區 | f_cost × 1.2 ≤ close < f_cost × 1.4 | ok |
| 極端高位區 | f_cost × 1.4 ≤ close < f_cost × 1.7 | warning |
| 韭菜收割區 | close ≥ f_cost × 1.7 | danger |

### 「主力」定義
三大法人合計：外資（Foreign_Investor）+ 投信（Investment_Trust）+ 自營商（Dealer）

### B2 指標（已規劃，分兩層）
- `signalB2`：純技術面（ATR、布林帶寬、收盤穩定度、量能百分位）
- `entryB2`：技術面 + 位階過濾（位階 ≥ 1.4× 外資成本 則不通過）

### 籌碼掃描（`/chip_scan`）
- 前端傳入股票代號清單 `codes`
- 後端逐檔用 FinMind `TaiwanStockInstitutionalInvestorsBuySell` 掃描
- 條件：外資買超 > `min_foreign` 且投信買超 > 0
- 回傳欄位：`code`、`name`、`close`、`foreign_net`、`trust_net`、`total_net`

### 即時資金雷達（`/flow/*`）
- 掃描範圍：上市＋上櫃
- 市場名單：FinMind `TaiwanStockInfo`
- 盤中即時價量：TWSE MIS，依市場自動組 `tse_XXXX.tw` / `otc_XXXX.tw`
- 產業資金流定義：
  - 漲 → 視為流入
  - 跌 → 視為流出
  - `amount = vol × price × 1000 / 1e8`
- 快取節奏：**3 分鐘**
- 產業卡會帶：
  - `net_amount`
  - `in_amount`
  - `out_amount`
  - `concentration`
  - `stock_count`
  - `prev_change`
- `/flow/stock/{code}` 會額外帶最近一筆法人資料到 `latest`

---

## 6. 主題與產業分類系統

後端維護三份對應表：

1. **`INDUSTRY_THEME`**：FinMind 產業類別 → 台股主題（例：半導體業 → [半導體, AI]）
2. **`STOCK_EXTRA_THEME`**：個股代號 → 額外主題（例：2330 → [CoWoS, 先進封裝, AI]）
3. **`THEME_US_STOCKS`**：台股主題 → 對應美股清單（用於連動分析）
4. **`CUSTOM_THEME_STOCKS`**：自訂主題個股清單（太空衛星、玻纖布、銅箔基板、被動元件）

---

## 7. AI 分析功能

- 端點：`POST /analyze`
- 輸入：股票代號、現價、外資成本、融資成本、外資動向、線型、對應美股表現
- 輸出：200字以內繁體中文段落分析（位階總結、法人籌碼、美股連動、操作建議 + 免責聲明）
- 快取：30分鐘，key = `{stock_code}_{current_price}`
- 模型：`claude-sonnet-4-20250514`

---

## 8. 環境變數與安全規則

⚠️ **重要**：以下 API Key 目前仍硬編碼在 `main.py` 中，**應搬移至 Railway 環境變數**：
```python
FINMIND_TOKEN    = os.environ.get("FINMIND_TOKEN")
FUGLE_API_KEY    = os.environ.get("FUGLE_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
DISCORD_WEBHOOK  = os.environ.get("DISCORD_WEBHOOK")
API_TOKEN        = os.environ.get("API_TOKEN", "0921")
```

API Key **絕對不可**出現在前端 HTML 或提交至 GitHub。

### Discord 推播規則
- Webhook：`DISCORD_WEBHOOK`
- 觸發端點：`POST /flow/monitor`
- 僅在**盤中 09:00–13:30** 自動推播
- 盤後仍可更新畫面，但**不推播**
- 同一個 3 分鐘 cache slot 內不重複推播同一訊號
- 訊息內容分開顯示：
  - `資料時間`
  - `推播時間`

---

## 9. 已知問題與待辦

| 問題 | 狀態 | 說明 |
|------|------|------|
| TWSE 端點 timeout | ⚠️ 已知 | MI_INDEX20、STOCK_DAY_ALL、T86 在 Lisa 的網路環境常 timeout；FinMind 為可靠後備 |
| API Key 暴露 | ⚠️ 待修 | 應改用 Railway 環境變數讀取 |
| Railway 伺服器區域 | 🔜 考慮中 | 考慮切換至新加坡/東京以降低台灣市場資料延遲 |
| 缺少本機依賴 | ⚠️ 已知 | 目前本機環境缺 `fastapi`、`uvicorn`、`httpx`，無法直接啟動整合測試 |
| VS Code / CLI 對話歷史不同步 | ⚠️ 已知 | 可能造成工作紀錄難追，需要另外保留 `md` 摘要 |

---

## 9-A. 待完善功能（源自 M哥 4/27 觀察示範文）

> 參考文章：M哥以**中美晶（5483）**為案例，示範完整觀察流程：10年月線 → 5年周線 → 2年日線 → 股權變化。以下為從該文提取、尚未實作的功能方向，依優先順序排列。

### 優先級 1｜融資性質判斷（B1 補強）

M哥區分「兩種融資」：

| 類型 | 特徵 | 意義 |
|------|------|------|
| 散戶融資 ❌ | 外資賣出時融資先進場，均線上方後融資撤退 | 危險訊號，主力在倒貨給融資 |
| 偽裝主力的融資 ✅ | 與外資同步進場，均線上方穩定持有 | 可接受，視為跟單行為 |

**待實作**：加入「融資動向警示」——近期融資增加 + 外資同步賣超 → 顯示警示標籤。資料來源已有（`/margin` + `/foreign`），為純前端邏輯。

### 優先級 2｜扣抵價計算（A 指標補強）

M哥最常用的兩個扣抵概念：

- **240日扣抵價**：判斷長期趨勢。扣抵價處於低位，代表未來幾週 240 日均線容易上翹（趨勢加速訊號）。
- **20日扣抵量**：判斷買點。扣抵量大，代表均量即將下降，量縮訊號即將出現。

**待實作**：用現有的歷史價量資料（`/price`）在前端計算扣抵價/扣抵量，補充到 A 指標顯示中。不需新 API。

### 優先級 3｜月線與周線位階（A 指標補強）

M哥完整觀察流程從大時間尺度開始：

1. **10年月線**：確認長期多頭基礎（是否站上 20 月線）
2. **5年周線**：確認「X型態」——下跌趨勢反轉後創一年新高的周線型態
3. **2年日線**：觀察 B2 進場點（量縮價穩）

**待實作**：計算月線 MA20 位階、判斷周線是否出現反轉型態，補充到 A 指標中。現有資料（`/price` 2年日線）只夠算月線，周線5年資料需確認 FinMind 是否支援更長區間。

### 優先級 4｜股權集中度變化（B1 補強）

M哥強調「大戶增加、散戶減少、股東人數急遽減少」是最重要的籌碼集中訊號，尤其在**創一年新高當下**，解套散戶大量出清，是籌碼再次淨化的關鍵時機。

**待實作**：串接 FinMind `TaiwanStockShareholding` 資料集，顯示大戶持股比例趨勢與股東人數變化。需確認 Backer 方案是否支援此資料集。

---

## 10. 技術決策紀錄

| 決策 | 選擇 | 原因 |
|------|------|------|
| 價格資料來源 | FinMind `TaiwanStockPrice` | Fugle 歷史資料為還原價，會造成現價顯示錯誤 |
| 外資成本基準 | 收盤價 | 最接近 籌碼K線 等參考 App，free data 最佳近似 |
| 主力定義 | 三大法人（外資+投信+自營） | 符合一般「主力成本」慣用定義 |
| FinMind 方案 | Backer（NT$699/月） | 支援全市場查詢（無需 data_id），為籌碼掃描必要條件 |
| 跨分頁 Token | sessionStorage + localStorage 雙存 | 確保跨分頁登入狀態一致 |
| 即時資金雷達快取 | 3 分鐘 | 前後端刷新節奏對齊，兼顧即時性與 API 壓力 |
| Discord 推播時段 | 僅盤中 | 避免盤後重複推播收盤資料造成誤判 |
| Discord 訊息時間欄位 | 資料時間 + 推播時間分開 | 避免把推播時間誤認為收盤/資料時間 |

---

## 11. 開發原則

- **迭代式開發**：建置 → 部署 → 觀察實際行為 → 修正
- **診斷優先**：修改前先用診斷腳本系統性測試 API 端點
- **參考 App 為真值**：以 籌碼K線、山竹股市 的顯示結果驗證計算準確度
- **Claude 作為雙重角色**：程式開發夥伴 + App 內建 AI 分析引擎
- **避免整檔重寫**：特別是 HTML/中文檔案，不要用整檔 UTF-8 重寫，以免造成亂碼
- **最小範圍 patch**：優先局部修改，降低編碼與副作用風險

---

*最後更新：2026-04-27｜已納入籌碼掃描、即時資金雷達 PRO、Discord 推播、3分鐘快取與盤中推播規則*
