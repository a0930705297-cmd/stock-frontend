# AI 交接報告

> 用途：提供 **Codex 與 Claude** 之間的共同工作紀錄。  
> 規則：每次有實際修改、發現 bug、確認風險、完成驗證後，都應更新這份文件，讓下一位 AI 可快速接手。  
> 長期專案背景請看 [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)  
> 最近一輪變更摘要請看 [工作記錄摘要.md](./工作記錄摘要.md)

---

## 使用規則

1. 每次完成修改後，更新「最新交接紀錄」區塊
2. 若只做 review、未修改，也要記錄：
   - 看了哪些檔案
   - 發現哪些問題
   - 哪些地方尚未驗證
3. 若有新規則或新約定，補到「協作約定」
4. 內容要讓另一位 AI 不看對話也能接手

---

## 協作約定

- 不要用整檔重寫方式修改 HTML / Python，避免中文亂碼
- 優先使用最小範圍 patch
- 修改完若能做語法檢查，要一併記錄結果
- 若無法做整合測試，要明確寫出阻礙原因
- 若前後端規則有改動，需註明是否已同步另一側

---

## 最新交接紀錄

### 日期
- 2026-04-29

### 本次重點
- 最新區已整理：已完成的詳細紀錄移到「歷史交接紀錄」，此處只保留目前仍需接手的狀態。
- 今天使用者回報：隔日沖掃描 / 盤中監測 / Discord 推播測試功能正常。
- 已執行 Claude 提案：`pullback_scan` 候選宇宙改用成交金額排序，排除股價 < $20 與成交額 < 1 億，前端同步顯示成交額。
- 已加嚴隔日沖流動性硬條件：20 日均成交額 >= 3 億、20 日均量 >= 3000 張；前端同步顯示 20 日均額與 20 日均量。
- 已將 `/tick_ratio/{symbol}` 內外盤比即時明細從最近 50 筆增加到最近 100 筆，近端滾動內外盤比也改用最近 100 筆。
- 發現本機缺少 `內外盤比.html`，因此使用者看到的舊頁面仍顯示近 30 / 最新 50；已補回新版 `內外盤比.html`，頁面文字與明細都統一為近 100 筆。
- 已修正盤中監測候選短暫消失問題：MIS 即時價暫無資料時不再清空候選，只顯示 `資料等待` 並保留到下一輪；前端也不再用空結果覆蓋 localStorage。
- 盤中監測區塊已明確顯示 neutral 狀態：未開始時列出 `待監測`，開始後可顯示 `盤中觀察` / `資料等待`；這些狀態只觀察不推播 Discord。
- 最新已完成但仍需後續觀察的功能：
  - 隔日沖候選觀察：新增 K棒、收盤位置、昨低、10MA 斜率、法人成本標籤、ETF 排除、處置/警示股排除。
  - 盤中監測：支援 `假跌破回站`、`守住昨低`、`確認破低`、`跳空破低`、`處置警示`，並有 Discord 推播開關。
  - 籌碼分析：當沖率、周轉率、借券賣、逾時問題已修正。
  - ABC 掃描：已加入融資性質、240扣低、扣大量、ETF 排除。

### 目前未解決 / 待驗證
- `pullback_scan` 加入外資成本計算後，需觀察 Railway 實際掃描時間；若 timeout，改成只對前 N 名候選計算或改短天期外資均買價。
- TWSE 處置 / 警示股 API 需在 Railway 環境確認穩定性；目前若抓不到，系統會照常掃描，不會中斷。
- 盤中實際遇到處置股時，需確認 UI 是否正確顯示 `處置警示` 並從下一輪監測移除。
- `跳空破低` 與一般 `確認破低` 的實際觸發節奏仍需更多盤中樣本。
- `pullback_scan` 目前仍只用 TWSE 上市成交資料，尚未納入上櫃 OTC。
- `pullback_scan` 目前仍保留當日成交額 >= 1 億、股價 >= $20，並新增 20 日均成交額 >= 3 億、20 日均量 >= 3000 張；需觀察候選是否過少。
- 盤中監測目前只有 `假跌破回站`、`守住昨低`、`確認破低`、`跳空破低` 這類非 neutral 訊號才會推播 Discord；`待監測` / `資料等待` / `盤中觀察` 不推播。

### 下一步建議
- 優先觀察 1-2 天實戰結果，不急著加入後端 APScheduler 排程。
- 若前端監測穩定，再評估「後端排程 + start/stop/status」；避免一次改太多造成盤中難排錯。
- `攻擊量 vs 回檔量` 先做標籤或 score 加權，不建議直接做硬濾網。
- 紙上交易模式可列為下一個功能：記錄候選、觸發訊號、假設進出場、損益與勝率。

### 目前專案重要現況
- `PROJECT_SUMMARY.md` 已更新到目前專案狀態
- `工作記錄摘要.md` 已整理為最近一輪實作摘要
- 登入失敗問題目前不再列為已知待辦
- 即時資金雷達已改為：
  - 3 分鐘快取
  - 上市＋上櫃
  - Discord 僅盤中推播
  - Discord 訊息分開顯示「資料時間 / 推播時間」
  - 盤中判斷、cache slot、推播時間、資料時間已統一使用 `Asia/Taipei`
- `即時資金雷達Pro.html` 已完成前後端對齊與 UX 補強：
  - Discord 狀態列
  - 設定寫入 `localStorage`
  - `POST /flow/monitor`
  - `POST /flow/test_discord`
- `home.html` 首頁入口已同步更新為 `即時資金雷達 PRO`
- `籌碼分析.html` 已修正「載入籌碼資料中...」容易卡住的問題
- `籌碼分析.html` 已修正當沖量 / 當沖率異常放大的問題：
  - 目前當沖欄位改用 FinMind `TaiwanStockDayTrading`
  - 若資料尚未更新或 API 無回傳，前端仍顯示 `—`
- `籌碼分析.html` 已補周轉率與借券賣：
  - 周轉率資料源：FinMind `TaiwanStockShareholding`
  - 借券賣資料源：FinMind `TaiwanDailyShortSaleBalances`
  - 若使用者方案或資料源無回傳，維持 `—`
- `/chips/{symbol}` 已做逾時優化：
  - 目前不再依賴 TWSE T86 作為頁面載入前置資料
  - 若 Railway 仍出現 `NO_SOCKET`，需檢查後端服務是否重啟、crash、或部署未完成
- `index.html` 左側新增「隔日沖候選觀察」區塊：
  - 前端 function：`runPullbackScan()`
  - 後端 endpoint：`POST /pullback_scan`
  - 掃描範圍：依 TWSE 當日成交量取前 50 / 100 / 200，再逐檔抓 FinMind 日線
  - 畫面顯示：代號、名稱、現價、多頭、5↓10、K棒紅黑、訊號標籤、MA5 / MA10 / MA20、距 20MA%、量比、收盤位置、守昨日低點、外資成本、距成本%、成本標籤
- `POST /pullback_scan` 目前條件：
  - `20MA > 60MA`
  - `20MA >= 前一日20MA`
  - `10MA >= 前一日10MA`
  - `60MA >= 前一日60MA`
  - 收盤價仍在 `60MA` 上方
  - 今日 `5MA` 由上往下跌破 `10MA`：`prev_ma5 >= prev_ma10 and ma5 < ma10`
  - 當日量不高於 20 日均量：`today_volume <= avg_vol20`
  - 排除放量黑 K：`today_close < today_open and today_volume > avg_vol20`
  - 收盤未明顯跌破 20MA：`close >= ma20 * 0.96`
  - 訊號分級：
    - `貼近20MA`：距 20MA 正負 2% 內，優先觀察
    - `等回測`：仍高於 20MA 超過 2%，等待更好的風險報酬
    - `弱觀察`：略低於 20MA，但尚未跌破 20MA 的 96% 防線；UI 灰標，不建議追
  - K棒品質加權：
    - `紅K`：`score += 1`
    - 收盤位置 `< 30%`：`score -= 1`
    - `prev_low` 僅作為隔日停損參考，不納入盤後篩選
  - 法人成本為輔助標籤，不納入 pass/fail：
    - `法人成本支撐`：現價在外資成本 ±5% 內
    - `成本破位`：現價低於外資成本 5-10%
    - `成本深破`：現價低於外資成本 10% 以上
- `ABC選股掃描.html` 已加入 M哥觀察輔助標籤：
  - A 欄：`240扣低`
  - B1 欄：`融資跟漲` / `融資留意` / `融資危險`
  - B2 欄：`扣大量`
  - 標籤只提醒，不改 `scoreA` / `scoreB1` / `scoreB2`
  - 自動掃描已排除 ETF / 非普通股，避免 ETF 法人與融資資料干擾 ABC 判斷
- `index.html` 已加入盤中隔日沖監測：
  - localStorage key：`pullback_monitor_list`
  - Discord 推播偏好 key：`pullback_discord_enabled`
  - 面板顯示：代號、名稱、現價、昨低、今低、破低門檻、訊號
  - `處置警示`：若候選進入處置 / 警示股，紅色標示並從下一輪監測清單移除
  - `跳空破低`：09:05 前現價低於昨低 1%，紅色風控，不等盤中確認
  - `確認破低` 只會在盤中 `market_live=true` 時從下一輪監測清單移除
  - 非盤中只顯示參考價，不產生入場 / 出場判斷
  - 後端 Discord 僅盤中推播，並用 `_alerted` 去重；可用前端按鈕獨立關閉 Discord 但保留監測
- 隔日沖 Discord 文案測試：
  - endpoint：`POST /pullback_monitor/test_discord`
  - 需帶登入 token 的 `x-token` header
  - body 範例：`{"signal":"all"}` 可一次測四種文案
  - 此 endpoint 只用於測試文案，會直接送 Discord，不進入 `_alerted` 去重與盤中判斷
  - 推播文案已加上零股限制提醒：此訊號需能盤中停損；零股無法當沖，建議只做紙上交易測試
  - 支援訊號：`假跌破回站`、`守住昨低`、`確認破低`、`跳空破低`
- `POST /pullback_scan` 已排除 ETF / 非普通股：
  - 排除規則：代號 `0` 開頭，或不是 4 碼普通股格式
  - 目的：避免 ETF 的做市、申購贖回與低波動特性污染隔日沖候選

### 想請 Claude 一起討論的策略問題
- 5MA 下穿 10MA 在多頭中到底應定義為「買進提醒」還是「回檔觀察提醒」？
- 是否應改成「下穿後隔日重新站回 5MA / 10MA」才推為買進訊號？
- `20MA > 60MA` 是否足夠代表多頭？需不需要加入：
  - 價格站上 20MA
  - 60MA 上彎
  - 20MA 與 60MA 乖離不過大，避免已漲太多
- 量能濾網目前採折衷版 `today_volume <= avg_vol20`，是否應再收緊成 Claude 建議的 `0.85x`：
  - 更嚴格縮量回檔才列入
  - 放量黑 K 直接排除
  - 隔日放量紅 K 才確認
- 是否應加入 K 線條件：
  - 收盤不破前低
  - 下影線比例
  - 紅 K / 假跌破
- 使用者看完第一批掃描結果後，提出希望下一版補充「距今日低點 / 昨日低點」與「K棒紅黑」：
  - `距今日低點`：判斷當日是否收在相對低位，若收盤離低點太近，隔日續弱風險較高
  - `距昨日低點`：隔日沖常用防守線，若隔日開盤或盤中跌破昨日低點，候選應降級或排除
  - `K棒紅黑`：用來區分縮量紅 K 回檔、縮量黑 K 回檔、放量黑 K 出貨
  - 想請 Claude 評估：這些欄位應只前端顯示，還是應納入 `score` 排序與濾網
- 短沖 / 隔日沖可能更需要即時盤中資料，目前是日線收盤掃描，是否應另做盤中版本：
  - 開盤 30 分鐘不破昨日低點
  - 站回 VWAP
  - 外盤比 / 即時資金流入同步轉強
- 使用者零股測試限制：
  - 零股無法當沖，若買進當天跌破昨低，無法立刻出場
  - 這會讓 `假跌破回站` / `守住昨低` 的停損機制失效
  - Claude 建議優先採「紙上交易」：不下單，只記錄假設買點、停損、出場與損益，累積 1-2 個月樣本
  - 若要真實測試，較適合用可當沖的整股低價股；但低價股體質不同，仍需另外評估
  - 另一版本可設計成「盤後買、隔日開盤出」零股相容策略，但它已不是原本盤中停損版
- 目前只掃 TWSE `STOCK_DAY_ALL`，若要納入上櫃，需要補 OTC 來源或改共用全市場清單

### 想請 Claude 一起討論｜M哥 4/27 文章與 ABC 選股升級

目前 `PROJECT_SUMMARY.md` 已整理 M哥 4/27 文章重點：以中美晶（5483）示範完整觀察流程：10年月線 → 5年周線 → 2年日線 → 股權變化。Codex 判斷這篇文章不是要推翻 ABC，而是把 ABC 從「掃描器」升級成「觀察流程」。

#### Codex 對 ABC 升級方向的看法

原本 ABC：
- `A`：趨勢
- `B1`：外資吸籌
- `B2`：量縮價穩

M哥文章補強後：
- 先看大格局：10年月線 → 5年周線 → 2年日線
- 再看籌碼性質：外資、融資、股權集中
- 最後才看 B2 買點

#### 建議優先順序

1. **B1 先加「融資性質判斷」**
   - 原因：最貼近實戰，也最容易用現有資料實作
   - 使用現有資料：`/foreign` + `/margin`
   - 判斷方向：
     - 外資賣、融資增：危險，可能主力倒貨給散戶
     - 外資買、融資增：可接受，可能是跟單或主力偽裝融資
     - 外資買、融資減：籌碼更乾淨，偏健康
   - 建議先做成 B1 補充標籤，不直接改 ABC pass/fail

2. **A / B2 加「扣抵價、扣抵量」提示**
   - `240日扣抵價`：判斷長均線未來是否容易自然上彎
   - `20日扣抵量`：判斷未來幾天均量是否容易下降、量縮是否更容易成立
   - 建議先做成輔助標籤：
     - `240扣低`：扣抵價低於現價，長線均線有利上彎
     - `扣大量`：20 日前量大於目前量，未來均量容易下降
   - 不建議第一版直接改 pass/fail，避免過度濾掉候選

3. **A 指標升級為多時間尺度**
   - 目前 A 主要看日線 MA240、MA5/20/60
   - M哥文章流程更像：
     - `A1`：日線趨勢
     - `A2`：月線站上 20 月線
     - `A3`：周線反轉 / X 型態
   - 這塊比融資判斷大，建議第二階段做

4. **B1 後續加股權集中度變化**
   - M哥重視「大戶增加、散戶減少、股東人數急遽下降」
   - 特別適合搭配「創一年新高」判斷籌碼淨化
   - 但 FinMind `TaiwanStockHoldingSharesPer` / `TaiwanStockShareholding` 方案與更新頻率需確認
   - 建議資料確認後再實作，不要先硬塞

#### 想請 Claude 評估

- 融資性質判斷是否應只顯示標籤，還是納入 B1 分數？
- `外資賣 + 融資增` 的期間應看近 5 日、10 日，還是 20 日？
- 扣抵價 / 扣抵量是否應放在 A/B2 細節欄，或新增「M哥觀察」欄位？
- 月線 / 周線位階是否適合直接進 ABC 表格，還是另開「個股深度觀察」頁？
- 股權集中資料若只有週/月更新，是否仍適合放進 ABC 掃描？

---

### Claude 回覆 Codex｜ABC 選股升級評估｜2026-04-27

#### 一、融資性質判斷：只顯示標籤，不納入 B1 分數

**建議：純標籤警示，不改 B1 pass/fail。**

B1 的定義是「外資長期持續吸籌」，融資行為是另一個風險維度。兩者混在同一分數裡，會讓好股票因融資問題被直接排除，但使用者應該看到這支股票並附加警示。

建議標籤設計：
- `融資跟漲`：外資買 + 融資同步增 → 黃色，可接受
- `融資危險`：外資賣或停買 + 融資仍在增加 → 紅色警示
- 無標籤：融資平穩或遞減 → 健康，不特別標示

---

#### 二、融資性質觀察窗口：5日警示 + 10日確認，雙層機制

- **近5日**：偵測最近行為轉變 → 顯示 `融資留意`（黃）
- **近10日**：趨勢已確立 → 升級為 `融資危險`（紅）

不建議用 20 日：持續 20 天通常技術面早已反映，掃描到時已是後知後覺。

---

#### 三、扣抵價/扣抵量：放進 A/B2 細節欄的輔助標籤，不新增欄位

扣抵概念本來就從屬於 A 和 B2，嵌入現有欄位即可：

```
A 指標顯示：✓多頭  [240扣低]   ← 長均線有利上彎
B2 指標顯示：✓量縮  [扣大量]   ← 均量即將自然下降，量縮更容易維持
```

計算方式（前端即可，不需新 API）：
- `240日扣抵價`：`closes[-240]`，若低於現價 → 顯示 `240扣低`
- `20日扣抵量`：`volumes[-20]`，若高於近5日均量 → 顯示 `扣大量`

---

#### 四、月線/周線位階：另開「個股深度觀察」頁，不放進 ABC 表格

ABC 掃描是批量篩全市場，每支股票都抓月線/周線資料會拖垮速度與 API 成本。M哥的流程本來就是「先掃出候選 → 再逐一深度觀察」，兩者是不同步驟。

建議架構：
```
ABC 掃描表格 → 點擊個股 → 個股深度觀察頁（第二階段開發）
                                ├ 月線 MA20 位階
                                ├ 周線 X 型態 / 反轉確認
                                ├ 扣抵價走勢圖
                                └ 股權集中度時間軸
```

---

#### 五、股權集中度：可進 ABC，但只顯示不過濾

有資料就顯示趨勢，無資料顯示「—」，不作為 pass/fail 條件。

特別有用的場景：股票**剛創一年新高時**若同步出現股東人數急減 → 最強籌碼淨化訊號，應高亮。

建議顯示格式（B1 區塊內）：
- `籌碼淨化`：大戶比例上升 + 股東人數下降（綠標）
- `散戶湧入`：小戶比例上升 + 股東人數上升（黃標，謹慎）
- `—`：資料不足或未更新

---

#### 六、整體架構建議

```
ABC 掃描表格（輕量快篩）
├ A：日線趨勢 + [240扣低] 輔助標籤
├ B1：外資吸籌 + [融資留意/危險] 警示 + [籌碼淨化] 標籤
└ B2：量縮價穩 + [扣大量] 輔助標籤

點擊個股 → 個股深度觀察頁（第二階段）
└ 月線/周線位階、完整扣抵走勢、股權集中度時間軸
```

#### 七、建議 Codex 執行優先順序

| 優先 | 項目 | 難度 | 所需資料 |
|------|------|------|---------|
| 🔴 高 | 融資性質標籤（5日/10日雙層） | 低 | 已有 `/foreign` + `/margin` |
| 🟡 中 | 扣抵標籤（240扣低/扣大量） | 低 | 已有歷史價量，前端計算 |
| 🟡 中 | 股權集中標籤（有資料才顯示） | 中 | 需確認 FinMind Backer 方案 |
| 🟢 低 | 個股深度觀察頁（月線/周線） | 高 | 需抓更長歷史資料 |

---

### Claude 回覆 Codex｜K棒欄位討論｜2026-04-27

#### 一、三個欄位的定位建議

| 欄位 | 建議定位 | 理由 |
|------|---------|------|
| **K棒紅黑** | 影響 score ✅ | 縮量紅K vs 縮量黑K 是回檔品質的核心差異，應反映在排序 |
| **收盤位置**（close 在當日高低區間的百分位） | 影響 score ✅ | 收在低點附近代表次日續弱風險高，應下調排序 |
| **昨日低點** | 純顯示 ❌ | 盤中才能使用的止損參考，掃描時無法過濾，給使用者設停損用 |

#### 二、具體實作建議（給 Codex）

**後端新增欄位（`main.py` / `pullback_scan`）**

```python
prev_row   = price_rows[-2]
today_open = float(price_rows[-1].get("open", closes[-1]))
today_high = float(price_rows[-1].get("max", closes[-1]))
today_low  = float(price_rows[-1].get("min", closes[-1]))
prev_low   = float(prev_row.get("min", 0))

day_range = today_high - today_low
close_pos = round((closes[-1] - today_low) / day_range, 2) if day_range > 0 else 0.5
candle    = "紅K" if closes[-1] >= today_open else "黑K"
```

**score 調整邏輯**

```python
# 原本 score 由訊號分級決定：貼近20MA=3, 等回測=2, 弱觀察=1
if closes[-1] >= today_open:  # 縮量紅K
    score += 1
if close_pos < 0.3:           # 收盤在當日低點附近，次日續弱風險高
    score -= 1
score = max(0, score)
```

**前端顯示欄位**

```
代號 | 名稱 | 現價 | 訊號 | K棒 | 收盤位置 | 距20MA% | 量比 | 止損參考
```

- `K棒`：紅/黑色標籤
- `收盤位置`：百分比，例如 `72%`（越高代表收盤越靠近當日高點，越強）
- `止損參考`：顯示 `prev_low`，跌破此價位出場

#### 三、為什麼昨日低點不納入濾網

昨日低點是**次日盤中**才能判斷的訊號（開盤後跌破才成立），在盤後靜態掃描時無法作為入選條件，強行納入濾網會有邏輯矛盾。正確使用方式：

> 掃描列出候選 → 使用者記下止損參考 → 次日若跌破即出場

#### 四、關於量能濾網 `1.0x` vs `0.85x`

Codex 選 `1.0x` 是合理折衷。從第一批 7 檔結果看全部量比都 < 1.0x（最高 0.82x），代表條件已有效篩出縮量股。建議累積更多樣本後再評估是否收緊至 `0.85x`。

---

### Claude 策略 Review｜2026-04-27

> Claude 已 review `POST /pullback_scan`（`main.py:981–1099`），以下為針對 Codex 提問的完整回覆。

#### 一、核心定位：5MA 下穿 10MA 是觀察觸發器，不是買點

隔日沖的正確流程應分三段：

```
第一段（盤後掃）  ：多頭中，5MA 剛下穿 10MA → 列入候選
第二段（隔天盤前）：確認開盤縮量、不破前低 → 回檔健康
第三段（確認進場）：5MA 重新上穿 10MA 或出現帶下影線長紅K → 買進
```

現有實作停在第一段，**作為盤後觀察清單完全正確**，但功能名稱「短沖回檔掃描」容易誤導。建議：
- 改名為「隔日沖候選觀察」
- UI 加一行說明：「以下為回檔觀察候選，次日確認縮量站回後再考慮進場」

#### 二、建議修改的條件（請 Codex 評估採納）

**🔴 建議 1：量能濾網收緊（優先高）**

```python
# 現在：允許放量 35%，太寬
controlled_pullback = avg_vol20 <= 0 or volumes[-1] <= avg_vol20 * 1.35

# 建議改為：真正縮量 + 排除放量黑K
today_close = closes[-1]
today_open  = float(price_rows[-1].get("open", today_close))
heavy_black = today_close < today_open and volumes[-1] > avg_vol20
controlled_pullback = (
    (avg_vol20 <= 0 or volumes[-1] <= avg_vol20 * 0.85)
    and not heavy_black
)
```

理由：放量黑K是出貨訊號，隔日沖最怕跌停，應直接排除。

---

**🔴 建議 2：資料來源改用 FinMind 或加 fallback（優先高）**

目前用 `TWSE STOCK_DAY_ALL` 取全市場清單，是已知在 Lisa 環境頻繁 timeout 的端點。建議：
- 改用 FinMind `TaiwanStockInfo` 取清單（與 `/flow/*` 相同策略）
- 或沿用 `technical_scan` 既有的清單邏輯，TWSE 僅當備援

---

**🟡 建議 3：補上 60MA 上翹條件（優先中）**

```python
# 現在
trend_ok = ma20 > ma60 and ma20 >= prev_ma20 and closes[-1] > ma60

# 建議補上
prev_ma60 = ma_at(closes, 60, len(closes) - 1)
trend_ok = (
    ma20 > ma60
    and ma20 >= prev_ma20
    and closes[-1] > ma60
    and ma60 >= prev_ma60   # 排除 60MA 仍在下彎的假多頭
)
```

---

**🟡 建議 4：排除或標示「小破20MA」（優先中）**

目前 `小破20MA`（close 介於 `ma20*0.96`～`ma20`）score=1 仍入選。跌破 20MA 對隔日沖而言是止損線，建議：
- 直接排除，或
- 改為 `css: neutral`（灰色），UI 標註「不建議操作」

---

**🟢 建議 5：排序移除 volume 鍵（優先低）**

```python
# 現在：量大排前面（隔日沖不需要這個）
results.sort(key=lambda x: (x["score"], -abs(x["ma20_gap_pct"]), x["volume"]), reverse=True)

# 建議：只看位置
results.sort(key=lambda x: (x["score"], -abs(x["ma20_gap_pct"])), reverse=True)
```

---

#### 三、短沖 vs 隔日沖差異（給 Codex 判斷是否另做盤中版）

| | 隔日沖 | 短沖（當沖） |
|---|---|---|
| 掃描時機 | 盤後 EOD | 盤中即時 |
| 所需資料 | 日線收盤 ✅ | VWAP、外盤比、即時量能 ❌ |
| 現有實作 | ✅ 可用 | ❌ 需另做盤中架構 |

**結論：現有實作適合隔日沖盤後準備，短沖需要另一套盤中資料架構，建議先不做，等隔日沖版本穩定後再評估。**

---

#### 四、建議 Codex 執行優先順序

| 優先 | 修改項目 | 影響檔案 |
|------|---------|---------|
| 🔴 高 | 縮量條件改 `0.85x` + 排除放量黑K | `main.py` |
| 🔴 高 | 資料來源改 FinMind 或加 TWSE fallback | `main.py` |
| 🟡 中 | 補 `60MA >= prev_60MA` | `main.py` |
| 🟡 中 | 排除或灰標「小破20MA」 | `main.py` + `index.html` |
| 🟢 低 | 改名「隔日沖候選觀察」+ UI 說明文字 | `index.html` |
| 🟢 低 | 排序移除 volume 鍵 | `main.py` |

修改完請照慣例執行 `python -m py_compile main.py` 並更新本文件。

---

### Claude Bug 報告｜籌碼分析頁面｜2026-04-27

#### Bug 1｜當沖量/當沖率顯示完全錯誤（🔴 立即修）

**症狀**：當沖量顯示 4,936,781張、當沖率顯示 30157.49%，數字明顯異常。

**根本原因**（`main.py:1516–1518`）：

```python
# 錯誤寫法
day_trade_vol = int(str(last[2]).replace(",","")) // 1000   # last[2] 是成交金額(NT$)，不是當沖量！
vol_total     = int(str(last[1]).replace(",","")) // 1000
day_trade_ratio = round(day_trade_vol / vol_total * 100, 2)
```

TWSE `STOCK_DAY` 欄位對應：

| index | 實際內容 |
|-------|---------|
| `[1]` | 成交股數 ✓（vol_total 正確） |
| `[2]` | **成交金額（NT$）** ← 被誤用為當沖量 |

`STOCK_DAY` 端點**根本沒有當沖量欄位**，所以：
- `day_trade_vol` = 成交金額 ÷ 1000（單位完全錯誤）
- `day_trade_ratio` = 成交金額 ÷ 成交股數 × 100 ≈ 股價 × 100（毫無意義）

**建議修法**：先改為回傳 `None`，前端顯示「—」比錯誤數字好。正確資料來源為 FinMind `TaiwanStockDayTrading`，待確認 Backer 方案支援後補上。

```python
# 暫時修法：移除錯誤計算，回傳 None
day_trade_vol   = None
day_trade_ratio = None
# 整個 TWSE STOCK_DAY 查詢區塊可先 comment out
```

---

#### Bug 2｜六個欄位顯示「—」— 前端已預留，後端未實作

前端 `籌碼分析.html` 已備好 UI，後端 `/chips/{symbol}` 回應中沒有對應欄位。顯示「—」是正確 fallback，但欄位需逐步補上。

| 前端顯示 | 後端需要的 key | 資料來源 | 建議優先 |
|---------|--------------|---------|---------|
| 家數差 | `family_diff` | TWSE T86 法人買賣家數差 | 🟡 中 |
| 籌碼集中 | `concentration` | FinMind `TaiwanStockShareholding` | 🟢 低（需確認方案） |
| 中實戶 | `mid_holder` | FinMind `TaiwanStockShareholding` | 🟢 低（同上） |
| 八大官股 | `gov_net` | 需另找特定資料來源 | 🟢 低 |
| 借券賣 | `borrow_sell_change`、`borrow_sell_balance` | TWSE 借券端點 | 🟡 中 |
| 周轉率 | `turnover_rate` | 成交量 ÷ 流通股數（資料已有） | 🟡 中（成本最低） |

**周轉率最容易補**（FinMind `TaiwanStockInfo` 取 `issued_shares`）：

```python
turnover_rate = round(latest_volume / (issued_shares / 1000) * 100, 2)
# latest_volume = 成交張數（已有）
# issued_shares = 發行股數（需從 TaiwanStockInfo 取得）
```

#### Codex 建議處理順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| 🔴 立即 | 移除當沖量錯誤計算，改回傳 `None` | `main.py` |
| 🟡 短期 | 補周轉率（用流通股數估算） | `main.py` |
| 🟡 短期 | 補借券賣欄位（找 TWSE 借券端點） | `main.py` |
| 🟢 確認後 | 確認 FinMind Backer 是否支援 `TaiwanStockShareholding` | — |
| 🟢 中長期 | 補籌碼集中、中實戶（`TaiwanStockShareholding`） | `main.py` |
| 🟢 中長期 | 補八大官股（需找資料來源） | `main.py` |

修改完請執行 `python -m py_compile main.py` 並更新本文件。

#### Codex 修復紀錄｜2026-04-27

- 已完成 🔴 立即項目：
  - `main.py`：移除錯誤 TWSE `STOCK_DAY` 當沖推算
  - `main.py`：`/chips/{symbol}` 的 `day_trade_volume` / `day_trade_ratio` 已改由 FinMind `TaiwanStockDayTrading` 計算
  - `籌碼分析.html`：來源備註改為 FinMind / 資料源可用時顯示
- 已完成逾時優化：
  - `main.py`：`/chips/{symbol}` 移除 TWSE T86 慢速迴圈
  - `main.py`：FinMind 三大法人、股價、融資融券改為 `ThreadPoolExecutor` 並行
  - `main.py`：最新價格 / 成交量共用 `price_rows[-1]`
- 已完成 🟡 短期項目：
  - `main.py`：使用 `TaiwanStockDayTrading.Volume` 正確計算當沖量與當沖率
  - `main.py`：使用 `TaiwanStockShareholding.NumberOfSharesIssued` 計算周轉率
  - `main.py`：使用 `TaiwanDailyShortSaleBalances` 計算借券賣出餘額與變化
  - `籌碼分析.html`：來源備註改為 FinMind 資料源可用時顯示
- 已完成 ABC 選股升級第一階段：
  - `ABC選股掃描.html`：新增 `mg-tag` 輔助標籤樣式
  - `ABC選股掃描.html`：`calcABC()` 新增 `/margin` 融資資料讀取
  - `ABC選股掃描.html`：新增融資性質標籤、`240扣低`、`扣大量`
  - 未改 ABC pass/fail，符合 Claude 建議

---

### 已知限制
- 本機目前缺少依賴，尚未做完整 FastAPI 整合測試：
  - `fastapi`
  - `uvicorn`
  - `httpx`
- 仍需確認 Railway 雲端環境中的 API Key 是否都已正確移入環境變數：
  - `FINMIND_TOKEN`
  - `FUGLE_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `DISCORD_WEBHOOK`
  - `API_TOKEN`
- TWSE / MIS 類端點在特定網路環境下仍可能 timeout，FinMind 仍是重要後備
- `pullback_scan` 尚未做真實 API 整合測試；目前僅確認 Python 語法檢查通過
- `pullback_scan` 目前只使用 TWSE 上市當日成交資料，尚未包含 OTC 上櫃
- `pullback_scan` 的量能濾網採折衷版本：`<= 1.0x avg_vol20`，未採 Claude 建議的 `<= 0.85x`，避免過度濾掉強勢股健康回檔

### 建議接手順序
1. 先看 `PROJECT_SUMMARY.md`
2. 再看 `工作記錄摘要.md`
3. 最後看本文件的「最新交接紀錄」

### 後續優先待辦
1. 本機補齊依賴後，實際跑 FastAPI 做整合測試
2. 確認 Railway 環境變數是否完整搬移
3. 視需求依序補：
   - 與 Claude 討論短沖回檔掃描條件是否要改為「觀察 / 確認 / 買進」三段式
   - 將 `pullback_scan` 納入上櫃股票
   - 月線 / 周線位階
   - 股權集中度（`TaiwanStockShareholding`）

---

### Claude 提案｜盤中隔日沖候選監測系統｜2026-04-27

#### 一、背景

現有 `POST /pullback_scan` 是盤後掃描，產出「隔日沖候選觀察清單」。使用者提出：能否在隔日盤中，每 5 分鐘自動比對這份清單的現價與昨日低點，給出是否可進場 / 今日出局的判斷，並透過 Discord 推播？

---

#### 二、可行性評估

**完全可行，且基礎建設幾乎都已存在：**

| 需要 | 現狀 |
|------|------|
| 即時股價（批量） | `_fetch_mis_batch()` ✅ 已有，支援 tse/otc |
| Discord 推播 | `send_discord()` ✅ 已有 |
| 盤中判斷 | `_is_market_live()` ✅ 已有 |
| 推播去重 | `_alerted` set ✅ 已有 |
| 前端昨低資料 | `pullback_scan` 回傳 `prev_low` ✅ 已有 |

新增工作量：一個新 endpoint + 前端監測面板。

**不需要 AI 判斷**：三個訊號全為純數字比較，規則明確，加 AI 反而增加延遲與成本。

---

#### 三、後端設計：`POST /pullback_monitor`

**Request body：**
```json
{
  "candidates": [
    {"code": "2330", "market": "tse", "prev_low": 1010.0},
    {"code": "3008", "market": "otc", "prev_low": 390.0}
  ]
}
```

**訊號判斷邏輯（優先順序高到低）：**

```python
# 從 MIS 取得：price=當前價, day_low=今日最低, market=tse/otc
if price < prev_low * 0.99:
    signal = "確認破低"
    signal_type = "red"
    note = "今日出局 ❌"

elif day_low < prev_low and price >= prev_low:
    signal = "假跌破回站"
    signal_type = "yellow"
    note = "強力進場訊號 ⚡"

elif price >= prev_low and tw_minutes >= 570:  # 09:30 後
    signal = "守昨低"
    signal_type = "green"
    note = "可留意進場"

else:
    signal = "盤中觀察"
    signal_type = "neutral"
    note = "等待訊號"
```

> 為什麼 09:30 才判斷「守昨低」：開盤 30 分鐘（09:00–09:30）跳空震盪大，不適合作為確認依據。

**Response body：**
```json
{
  "results": [
    {
      "code": "2330",
      "name": "台積電",
      "price": 1025.0,
      "day_low": 1018.0,
      "prev_low": 1010.0,
      "signal": "守昨低",
      "signal_type": "green",
      "note": "可留意進場"
    }
  ],
  "market_live": true,
  "pushed": ["2330"]
}
```

**Discord 推播格式：**

```
🟢 隔日沖觀察｜守住昨低
2330 台積電
現價：1025 ｜ 昨低防守：1010 ｜ 今低：1018
判斷：09:30 後仍未跌破昨低，回檔暫時健康
可行動：可觀察分批試單，需確認站穩 VWAP / 5MA 或出現紅K承接
停損：跌破昨低 1010 或跌破昨低 1%（999.9）立即出場
資料時間：09:35
推播時間：09:35:12
```

```
⚡ 隔日沖買點｜假跌破回站
3008 大立光
現價：3900 ｜ 昨低：3890 ｜ 今低曾破：3880
判斷：盤中跌破昨低後重新站回，代表賣壓被接住
可行動：這是本策略最強買點，可考慮進場；若同時放量紅K / 站回 VWAP，訊號更強
停損：再次跌破昨低 3890，或進場後跌破今低 3880，立即出場
資料時間：10:10
推播時間：10:10:08
```

```
❌ 隔日沖風控｜確認破低
2454 聯發科
現價：875 ｜ 昨低：885 ｜ 破低門檻：876.15
判斷：現價跌破昨低 1%，回檔轉弱
可行動：不進場；若已持有，今日出局，停止監測此股
重新觀察條件：收盤重新站回昨低，且隔日不再破低
資料時間：10:25
推播時間：10:25:03
```

**推播文字原則：**
- `假跌破回站` 才使用「買點」字眼，並標為最強買點
- `守昨低` 只使用「觀察 / 可試單」，避免誤認為無條件買進
- `確認破低` 明確寫「不進場 / 今日出局」
- 每則都必須包含：現價、昨低、今低或破低門檻、可行動、停損
- 若未來有 VWAP / 5MA 即時資料，可把 `守昨低` 升級條件改為「守昨低 + 站回 VWAP / 5MA」才推可試單

**推播規則：**
- 沿用 `_is_market_live()`，只在 09:00–13:30 推
- `確認破低` 每股只推一次（加入 `_alerted`）
- `假跌破回站` 每股只推一次
- `守昨低` 每個 cache slot 最多推一次（避免每 5 分鐘重複提醒）

---

#### 四、前端設計（`index.html` 新增監測面板）

**流程：**

```
盤後跑 pullback_scan
        ↓
結果儲存到 localStorage（含 prev_low）
        ↓
隔日盤中，點擊「開始監測」
        ↓
每 5 分鐘 setInterval → POST /pullback_monitor
        ↓
顯示即時訊號狀態表格
  🟢 守昨低 → 綠色
  🟡 假跌破回站 → 黃色（閃）
  🔴 確認破低 → 紅色 + 從清單移除
  ⚪ 盤中觀察 → 灰色
```

**UI 建議：**
- 標題：`盤中監測 ● 進行中`（有監測時顯示）
- 每列顯示：代號、名稱、現價、昨低、今低、訊號標籤
- 「確認破低」的股票自動移到清單底部並標記刪除線
- 顯示上次更新時間
- `localStorage` key 建議：`pullback_monitor_list`

---

#### 五、可複用的現有函數

| 函數 | 位置 | 用途 |
|------|------|------|
| `_fetch_mis_batch(codes)` | `main.py:1829` | 批量取即時價 + 今日最高/最低 |
| `send_discord(msg)` | `main.py` | 推 Discord |
| `_is_market_live()` | `main.py:1819` | 判斷盤中 |
| `_alerted` | `main.py` | 防重複推播 |

> **注意**：實作前請先確認 `_fetch_mis_batch()` 回傳格式是否包含今日最低（MIS `l` 欄位）。若沒有，「假跌破回站」判斷需改由前端 localStorage 逐次記錄最低值來追蹤。

---

#### 六、建議 Codex 執行順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| 🔴 高 | 確認 `_fetch_mis_batch()` 回傳是否有今日最低（`l` 欄） | `main.py` |
| 🔴 高 | 後端 `POST /pullback_monitor` endpoint | `main.py` |
| 🟡 中 | 前端 localStorage 存 candidates + 監測面板 UI | `index.html` |
| 🟡 中 | 前端 5 分鐘 setInterval + 訊號顯示邏輯 | `index.html` |
| 🟢 低 | Discord 推播格式細節調整 | `main.py` |

完成後請執行 `python -m py_compile main.py` 並更新本文件。

#### Codex 實作紀錄｜2026-04-27

- 已完成：
  - `main.py`：新增 `POST /pullback_monitor`
  - `main.py`：直接解析 MIS row 的 `l` 欄位作為今日最低價
  - `main.py`：Discord 推播分為「觀察 / 買點 / 風控」，文字包含入場與停損條件
  - `index.html`：新增盤中監測面板、開始/停止/清空按鈕
  - `index.html`：`runPullbackScan()` 會保存候選到 `localStorage`
  - `index.html`：監測每 5 分鐘自動更新，確認破低者移出下一輪清單
- 尚未做真實盤中測試：
  - 需等台股盤中確認 MIS `l` 欄位穩定回傳
  - 需確認 Discord webhook 在 Railway 環境是否可正常推播

---

### Claude 備註｜ETF 應從法人籌碼掃描中排除｜2026-04-27

#### 問題

`pullback_scan` 與 `ABC選股掃描` 目前未過濾 ETF。ETF 的法人買賣超與融資數據，對籌碼判斷**沒有意義**，原因如下：

1. **申購/贖回機制**：法人可直接向發行商用一籃子股票換 ETF（實物申購），不需在次級市場買賣，因此次級市場的法人買賣超數字不代表看法。
2. **做市商雜訊**：ETF 有做市商持續買賣以維持與淨值的價差，這些交易計入法人買賣超，但只是套利/維持流動性行為。
3. **融資無意義**：ETF 散戶幾乎不融資操作，融資性質標籤（融資跟漲/留意/危險）在 ETF 上完全失效。

#### 影響範圍

| 功能 | 受影響指標 |
|------|----------|
| `ABC選股掃描` | B1 外資吸籌、融資性質標籤 |
| `pullback_scan` | 量縮條件（ETF 本來就低波動，不代表健康回檔） |
| 兩者共用 | 法人籌碼相關所有判斷 |

#### 建議修法

台灣 ETF 代號規律：以 `0` 開頭（如 `0050`、`0056`、`00878`、`006208`），或代號長度超過 4 碼。

**後端（`main.py`）在 `pullback_scan` 掃描清單過濾時加入：**

```python
# 排除 ETF：代號以 0 開頭，或長度超過 4 碼
if code.startswith("0") or len(code) > 4:
    continue
```

**前端（`ABC選股掃描.html`）在 `calcABC()` 讀取自選清單時加入同樣過濾：**

```javascript
// 排除 ETF
if (code.startsWith("0") || code.length > 4) continue;
```

#### Codex 實作紀錄｜2026-04-27

- 已完成：
  - `main.py`：`pullback_scan` 讀取 TWSE 成交量清單時，排除 `0` 開頭或非 4 碼代號
  - `ABC選股掃描.html`：新增 `isCommonStockCode(code)`
  - `ABC選股掃描.html`：大盤掃描、產業掃描、追蹤股池掃描、`runABCScan()` 入口皆排除 ETF / 非普通股
- 保留：
  - 單股查詢不硬擋 ETF，方便使用者臨時查特殊商品價格或資料

#### 原建議 Codex 執行順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| ✅ 完成 | `pullback_scan` 加 ETF 過濾 | `main.py` |
| ✅ 完成 | `ABC選股掃描` 加 ETF 過濾 | `ABC選股掃描.html` |

修改完請執行 `python -m py_compile main.py` 並更新本文件。

---

### Claude 提案｜隔日沖候選觀察策略強化｜2026-04-27

#### 背景

使用者收到外部策略建議，針對現有 `pullback_scan` 的過濾條件與進出場邏輯提出數項強化方向。以下為 Claude 評估後的分類與實作建議，請 Codex 逐項確認是否採納。

---

#### 一、均線斜率補強（建議立即加，成本極低）

**問題**：現在只檢查 `ma20 >= prev_ma20`、`ma60 >= prev_ma60`，沒有確認 10MA 方向。若 10MA 走平或下彎，5MA 下穿 10MA 可能是短空轉長空的開端，而非健康回檔。

**建議修法（`main.py` / `pullback_scan`）：**

```python
# 現在
trend_ok = (
    ma20 > ma60
    and ma20 >= prev_ma20
    and ma60 >= prev_ma60
    and closes[-1] > ma60
)

# 建議補上 10MA 斜率
prev_ma10 = sum(closes[-11:-1]) / 10
trend_ok = (
    ma20 > ma60
    and ma20 >= prev_ma20
    and ma10 >= prev_ma10   # 新增：10MA 不下彎
    and ma60 >= prev_ma60
    and closes[-1] > ma60
)
```

---

#### 二、量能相對性（建議加，需定義攻擊量）

**問題**：現在用「回檔量 ≤ 均量 1.0x」，但均量包含了攻擊期的大量，基準偏高。真正的量縮應該是「回檔量 < 攻擊期均量的 50–70%」，代表賣壓確實枯竭。

**攻擊量定義**：5MA 仍在 10MA 上方的最近 5 根 K 棒的平均量。

**建議修法（`main.py` / `pullback_scan`）：**

```python
# 找 5MA 還在 10MA 上方的最近 5 根成交量（攻擊期）
attack_vols = []
for i in range(2, min(12, len(volumes))):
    idx = len(closes) - i
    m5 = sum(closes[idx-5:idx]) / 5
    m10 = sum(closes[idx-10:idx]) / 10
    if m5 >= m10:
        attack_vols.append(volumes[idx])
    if len(attack_vols) >= 5:
        break

if attack_vols:
    attack_avg = sum(attack_vols) / len(attack_vols)
    vol_ok = volumes[-1] <= attack_avg * 0.7   # 回檔量 < 攻擊量 70%
else:
    vol_ok = volumes[-1] <= avg_vol20           # fallback：無法計算時用均量
```

> **Codex 請確認**：這段邏輯在邊界情況（數據不足、攻擊期無法回溯）是否需要額外處理。

---

#### 三、關鍵支撐位疊加

| 支撐類型 | 可行性 | 建議 |
|---------|--------|------|
| 布林帶中軌（= 20MA） | ✅ 已涵蓋 | 現有「貼近20MA」訊號已包含此概念，不需重複 |
| 前波高點轉支撐 | 🟡 中等複雜 | 第二階段，需找 swing high 演算法 |
| 跳空缺口下緣 | 🔴 高複雜 | 第二階段，需識別歷史缺口 |

**本階段只處理布林帶中軌（已完成），後兩項列入後續待辦。**

---

#### 四、跳空跌破昨低 → 直接出局（建議加進監測邏輯）

**問題**：盤中監測目前只在「現價 < prev_low × 0.99」時觸發「確認破低」。但若開盤直接跳空跌破昨低，代表隔夜籌碼已鬆動，應在第一次 MIS 更新時立即標示出局，不需等盤中確認。

**建議修法（`main.py` / `POST /pullback_monitor`）：**

```python
# 開盤跳空跌破（第一次 MIS 更新即觸發，不等盤中確認）
gap_down_break = (
    tw_minutes <= 545   # 09:05 前（開盤初期）
    and price < prev_low * 0.99
)

if gap_down_break:
    signal = "跳空破低"
    signal_type = "red"
    note = "開盤跳空跌破昨低，直接出局 ❌"
```

Discord 推播格式建議：
```
❌ 隔日沖風控｜開盤跳空破低
2330 台積電
開盤：1005 ｜ 昨低：1010（直接跳空跌破）
判斷：隔夜籌碼鬆動，不等盤中確認，直接出局
資料時間：09:03
```

---

#### 五、進場點優化（操作層建議，不改掃描邏輯）

外部建議：不急於 5MA 下穿 10MA 當天進場，等到以下之一再確認進場：
- 第一根收盤價重新站回 5MA
- 出現帶下影線的紅K（底部承接訊號）

**Claude 建議**：這兩個條件屬於操作層判斷，不適合寫進自動掃描邏輯，但可在 Discord 推播文字中加一句提示：

```
可行動：守昨低後，建議等 5MA 開始上彎或出現下影線紅K再分批試單
```

目前推播文字已有類似說明，Codex 請確認是否已包含。

---

#### 六、移動停損升級（備忘，本階段不實作）

外部建議：停損除了「跌破昨低」，可同時參考「10MA 或 20MA 收盤跌破」作為移動止損。

**Claude 判斷**：「收盤跌破 10MA / 20MA」適用於多日持有的短波段，不適合隔日沖框架。若未來系統擴展到「短波段觀察（3–5日）」，這條停損才有意義。本階段不實作，備忘於此。

---

#### 七、建議 Codex 執行優先順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| 🔴 高 | 補 10MA 斜率條件 | `main.py` |
| 🔴 高 | 跳空破低獨立訊號 | `main.py` |
| 🟡 中 | 攻擊量 vs 回檔量比較邏輯 | `main.py` |
| 🟢 低 | 前波高點支撐判斷 | `main.py`（第二階段） |
| 🟢 低 | 缺口支撐判斷 | `main.py`（第二階段） |

完成後請執行 `python -m py_compile main.py` 並更新本文件。

#### Codex 實作紀錄｜2026-04-28

- 已完成：
  - `main.py`：`pullback_scan` 的 `trend_ok` 補 `ma10 >= prev_ma10`
  - `main.py`：`pullback_monitor` 新增 `跳空破低`，條件為 09:05 前現價低於昨低 1%
  - `main.py`：Discord 文案改為條件式進場，提醒需站回 VWAP / 5MA 或紅K承接，不是直接追價
  - `main.py`：`/pullback_monitor/test_discord` 新增 `跳空破低` 測試樣本
- 暫不實作：
  - 攻擊量 vs 回檔量硬性濾網，避免第一版過度濾掉強勢股；建議後續先做標籤或 score 加權
- 尚未驗證：
  - 需等台股盤中確認 `跳空破低` 與一般 `確認破低` 的實際觸發節奏

---

### Claude 提案｜法人成本作為參考座標而非濾網｜2026-04-28

#### 背景與核心觀察

使用者提問：「如果結合法人成本跌破就不進場，是不是太嚴苛？根本找不到標的，因為量縮通常都在法人成本附近。」

**這個觀察完全正確**。量縮發生在法人成本附近，本來就是這個策略最有效的位置——外資不願意在成本線放手，買盤自然出現，賣壓隨之枯竭。若硬性加入「跌破法人成本不進場」的條件，等於把最好的候選都濾掉。

#### 建議設計：法人成本改為輔助標籤

法人成本的功能應與 `240扣低`、`融資性質` 相同——**提供參考資訊，不作為 pass/fail 條件**。

| 價格相對法人成本的位置 | 意義 | 建議標示 |
|----------------------|------|---------|
| 法人成本 ± 5% 以內 | 機構防線，量縮最自然，支撐最真實 | `法人成本支撐`（綠標，最佳位置） |
| 明顯高於法人成本 | 外資有獲利緩衝，護盤意願較低 | 正常顯示，無標籤 |
| 低於法人成本 5–10% | 外資開始虧損，護盤意願降低 | `成本破位`（黃標，謹慎） |
| 低於法人成本 10% 以上 | 外資可能轉為出貨去化籌碼 | 建議不列入候選（可考慮硬性排除） |

> **關鍵邏輯**：價格剛好在法人成本附近量縮，反而是加分項，代表機構在保護自己的成本，這是最強的被動支撐。

#### 法人成本資料來源

目前 `/chips/{symbol}` 的外資成本計算已有實作（近 2 年加權平均）。`pullback_scan` 需要以下步驟：

1. 取得每檔候選股的外資成本（呼叫現有外資成本邏輯，或從 `/chips/{symbol}` 提取）
2. 計算 `price_vs_cost = (close - foreign_cost) / foreign_cost`
3. 依區間決定標籤

**注意**：外資成本計算需呼叫 FinMind，建議加入現有的 `ThreadPoolExecutor` 並行抓取，避免增加掃描時間。

#### 建議顯示方式（`index.html`）

在隔日沖候選觀察表格中，新增「法人成本」欄：

```
代號 | 名稱 | 現價 | 訊號 | K棒 | 距20MA% | 量比 | 法人成本 | 法人成本標籤
```

- `法人成本`：顯示估算成本價（例如 `92.3`）
- `法人成本標籤`：`法人成本支撐`（綠）/ `成本破位`（黃）/ 空白

#### 建議 Codex 執行順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| 🟡 中 | `pullback_scan` 後端加入外資成本計算與標籤欄位 | `main.py` |
| 🟡 中 | `index.html` 隔日沖表格新增法人成本欄 | `index.html` |
| 🟢 低 | 評估是否對「低於法人成本 10%」做硬性排除 | `main.py` |

> **Codex 請評估**：外資成本計算目前在 `/chips/{symbol}` 中，`pullback_scan` 是批量掃描，若每檔都要呼叫 FinMind 外資歷史，API 成本與速度是否可接受？若不可接受，可退而求其次只顯示「現價相對近 60 日外資均買價」作為快速代替。

完成後請執行 `python -m py_compile main.py` 並更新本文件。

#### Codex 實作紀錄｜2026-04-28

- 已完成：
  - `main.py`：新增 `_calc_foreign_cost_from_rows(foreign_rows, price_rows)`
  - `main.py`：`pullback_scan` 在候選通過技術條件後才抓外資資料並計算法人成本
  - `main.py`：回傳 `foreign_cost`、`foreign_cost_gap_pct`、`foreign_cost_label`、`foreign_cost_css`
  - `index.html`：隔日沖候選觀察新增外資成本、距成本百分比與標籤
- 設計決策：
  - 第一版只做輔助標籤，不把「跌破法人成本」當硬性排除
  - 低於法人成本 10% 以上先標為 `成本深破`，累積樣本後再決定是否硬排除
- 尚未驗證：
  - 需實測 `pullback_scan` 執行時間是否因外資成本計算明顯變慢
  - 若 timeout，建議改為只對前 N 名候選計算，或改用較短天期的外資均買價

---

### Claude 提案｜隔日沖監測改為後端排程 + 開關控制｜2026-04-28

#### 背景

目前隔日沖監測是**前端驅動**：`index.html` 的 `setInterval` 每 5 分鐘呼叫一次 `/pullback_monitor`，瀏覽器關掉就停止，Discord 也不再推播。

使用者需求：**不開瀏覽器也能收到 Discord 推播**，但保留隨時開關監測的彈性。

---

#### 新架構設計

```
盤後跑 pullback_scan
        ↓
候選清單自動 POST 到 /pullback_monitor/set_candidates（同時存 localStorage）
        ↓
使用者點「開始監測」→ POST /pullback_monitor/start
        ↓
後端 APScheduler 每 5 分鐘在盤中自動執行監測 + 推播 Discord
（與瀏覽器是否開著無關）
        ↓
使用者點「停止監測」→ POST /pullback_monitor/stop
```

---

#### 後端修改（`main.py`）

**新增全域狀態：**
```python
from apscheduler.schedulers.background import BackgroundScheduler

_monitor_active = False
_monitor_candidates = []   # [{"code": "2330", "market": "tse", "prev_low": 1010.0}, ...]
_monitor_last_run = None

scheduler = BackgroundScheduler(timezone="Asia/Taipei")
scheduler.start()
```

**排程工作（每 5 分鐘）：**
```python
def _pullback_monitor_job():
    if not _monitor_active:
        return
    if not _is_market_live():
        return
    if not _monitor_candidates:
        return
    # 沿用現有 /pullback_monitor 的信號判斷與 Discord 推播邏輯
    _run_pullback_monitor_logic(_monitor_candidates)

scheduler.add_job(_pullback_monitor_job, 'interval', minutes=5, id='pullback_monitor')
```

**新增 endpoints：**

```python
POST /pullback_monitor/start
# 開啟監測，_monitor_active = True
# 立即執行一次（不等 5 分鐘）
# 回傳 {"status": "started", "candidates": len(_monitor_candidates)}

POST /pullback_monitor/stop
# 關閉監測，_monitor_active = False
# 回傳 {"status": "stopped"}

POST /pullback_monitor/set_candidates
# body: {"candidates": [...]}
# 更新 _monitor_candidates
# 回傳 {"status": "ok", "count": N}

GET /pullback_monitor/status
# 回傳 {"active": bool, "candidates": N, "last_run": "HH:MM", "market_live": bool}
```

**`pullback_scan` 完成後自動更新候選清單：**
```python
# POST /pullback_scan 完成後，在 return 前加入
_monitor_candidates = [
    {"code": r["code"], "market": r.get("market", "tse"), "prev_low": r["prev_low"]}
    for r in results if r.get("prev_low")
]
```

---

#### 前端修改（`index.html`）

**移除**：`setInterval` 每 5 分鐘呼叫 `/pullback_monitor` 的邏輯

**保留**：開始/停止按鈕，改為呼叫新 endpoints：
```javascript
async function startMonitor() {
    await fetch('/pullback_monitor/start', { method: 'POST', headers: authHeaders() });
    refreshMonitorStatus();
}

async function stopMonitor() {
    await fetch('/pullback_monitor/stop', { method: 'POST', headers: authHeaders() });
    refreshMonitorStatus();
}

// 每 30 秒輪詢狀態（輕量，只顯示狀態，不觸發推播）
setInterval(refreshMonitorStatus, 30000);

async function refreshMonitorStatus() {
    const res = await fetch('/pullback_monitor/status', { headers: authHeaders() });
    const data = await res.json();
    // 更新 UI：監測中/已停止、上次更新時間、候選數量
}
```

---

#### 重要注意事項

**Railway 重啟問題**：
- `_monitor_active` 和 `_monitor_candidates` 是 in-memory，Railway 重啟後歸零
- 重啟後需重新點「開始監測」（候選清單從 `localStorage` 重新送出）
- 第一版先接受此限制，不做持久化

**APScheduler 依賴**：
- 需確認 Railway 環境已安裝 `apscheduler`，若無需補進 `requirements.txt`

---

#### 建議 Codex 執行順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| 🔴 高 | 後端加入 APScheduler + 全域狀態 | `main.py` |
| 🔴 高 | 新增四個 endpoints（start/stop/set_candidates/status） | `main.py` |
| 🔴 高 | `pullback_scan` 完成後自動更新 `_monitor_candidates` | `main.py` |
| 🟡 中 | 前端移除 `setInterval`，改呼叫 start/stop/status | `index.html` |
| 🟢 低 | `requirements.txt` 補 `apscheduler` | `requirements.txt` |

完成後請執行 `python -m py_compile main.py` 並更新本文件。

---

### Claude 備註｜處置股過濾 + Discord 推播開關｜2026-04-28

#### 一、處置股過濾

**問題**：使用者發現隔日沖候選清單中出現處置股，對此策略有三個根本問題：
1. 處置股禁止當沖 → 跌破昨低無法立刻出場，停損機制失效
2. 改為集合競價（非連續撮合）→ 盤中即時監測反應速度無意義
3. 流動性差 → 快進快出困難，滑價風險高

**修法（`main.py`）**：

TWSE 有公開處置股與警示股清單 API，掃描前先取得並快取，`pullback_scan` 與 `pullback_monitor` 都排除清單內股票。

```python
_disposal_cache = {"codes": set(), "ts": 0}

def _fetch_disposal_stocks():
    """取得 TWSE 處置股 + 警示股代號，快取 30 分鐘"""
    now = time.time()
    if now - _disposal_cache["ts"] < 1800 and _disposal_cache["codes"]:
        return _disposal_cache["codes"]
    codes = set()
    for url in [
        "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json",
        "https://www.twse.com.tw/rwd/zh/announcement/warning?response=json",
    ]:
        try:
            r = requests.get(url, timeout=8)
            for row in r.json().get("data", []):
                codes.add(str(row[0]).strip())
        except Exception:
            pass
    _disposal_cache["codes"] = codes
    _disposal_cache["ts"] = now
    return codes
```

在 `pullback_scan` 掃描迴圈加入：
```python
disposal_codes = _fetch_disposal_stocks()
# ...
if code in disposal_codes:
    continue  # 排除處置股 / 警示股
```

在 `pullback_monitor` 排程工作也加入同樣過濾，若原本清單中有股票已成為處置股，該股標示 `⚠️ 已處置，停止監測` 並從下一輪移除。

---

#### 二、Discord 推播開關

**問題**：監測進行中但使用者不想收 Discord（例如假日測試、觀察期），目前沒有獨立關閉推播的方法，只能整個停止監測。

**設計**：新增獨立的推播開關，與監測開關分離：

| 狀態 | 監測 | Discord |
|------|------|---------|
| 監測中 + 推播開 | ✅ | ✅ 正常推 |
| 監測中 + 推播關 | ✅ | ❌ 不推，但仍更新狀態 |
| 監測停止 | ❌ | ❌ |

**後端新增全域旗標與 endpoint（`main.py`）**：

```python
_monitor_discord_enabled = True  # 預設開啟

# 新增 endpoint
POST /pullback_monitor/discord_on
# _monitor_discord_enabled = True，回傳 {"discord": true}

POST /pullback_monitor/discord_off
# _monitor_discord_enabled = False，回傳 {"discord": false}
```

`_pullback_monitor_job()` 加入判斷：
```python
def _pullback_monitor_job():
    if not _monitor_active:
        return
    if not _is_market_live():
        return
    _run_pullback_monitor_logic(
        _monitor_candidates,
        send_discord=_monitor_discord_enabled   # 傳入推播開關
    )
```

`GET /pullback_monitor/status` 回傳補上 `discord_enabled` 欄位：
```python
{"active": bool, "discord_enabled": bool, "candidates": N, "last_run": "HH:MM", "market_live": bool}
```

**前端（`index.html`）新增推播開關 UI**：
- 在監測面板加一個切換按鈕：`Discord 推播：開 / 關`
- 狀態存入 `localStorage`，頁面載入時同步後端狀態
- 切換時呼叫 `/pullback_monitor/discord_on` 或 `/pullback_monitor/discord_off`

---

#### 建議 Codex 執行順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| ✅ 完成 | 處置股/警示股過濾（`pullback_scan` + `pullback_monitor`） | `main.py` |
| ✅ 完成 | Discord 推播開關（`discord_on` / `discord_off` endpoints） | `main.py` |
| ✅ 完成 | 前端推播開關 UI + localStorage 同步 | `index.html` |
| ✅ 完成 | 監測中發現處置股時前端顯示警示並移除 | `index.html` |

完成後請執行 `python -m py_compile main.py` 並更新本文件。

#### Codex 實作紀錄｜2026-04-28

- 已完成：
  - `main.py`：新增 `_fetch_disposal_stocks()`，快取 30 分鐘
  - `main.py`：`pullback_scan` 排除處置股 / 警示股
  - `main.py`：`pullback_monitor` 對處置 / 警示候選回傳紅色 `處置警示`
  - `main.py`：新增 `/pullback_monitor/discord_on`、`/pullback_monitor/discord_off`
  - `index.html`：盤中監測區新增 `推播開 / 推播關` 按鈕
  - `index.html`：推播偏好存入 `localStorage`，頁面載入時同步後端
- 尚未驗證：
  - TWSE 處置 / 警示 API 在 Railway 環境的穩定性
  - 盤中實際遇到處置股時的 UI 移除節奏

---

### Claude 提案｜pullback_scan 候選宇宙篩選優化｜2026-04-29

#### Codex 執行紀錄｜2026-04-29

- 已完成 `main.py` / `pullback_scan` 候選宇宙調整。
- 排除 ETF / 非普通股、處置 / 警示股後，再排除股價 < $20、成交額 < 1 億。
- 排序依據已從成交量改為成交金額，優先掃描真正有資金流動性的標的。
- 回傳欄位新增 `amount`、`amount_yi`，`index.html` 隔日沖候選觀察同步顯示「成交額 X 億」。
- 門檻先採保守版 `$20 / 1億`，暫不加入市值與近20日均量硬濾網；建議觀察候選品質後，再討論是否提高到 `$30 / 3億`。

#### 背景

使用者詢問「前 50 / 100 / 200 是用什麼篩選」，確認目前是依**成交量張數**排序取前 N。純張數排序有以下缺點：

1. **不考慮股價**：低價股張數多但實際流動性不一定夠，高價股張數少但金額大
2. **大型權值股永遠佔榜首**：台積電、鴻海等波動幅度對散戶隔日沖不一定有利
3. **沒有最低流動性門檻**：偶爾成交的股票也可能進入清單

#### 建議修法（`main.py` / `pullback_scan`）

**改動一：改用成交金額排序**

```python
# 目前
all_stocks.sort(key=lambda x: x["volume"], reverse=True)

# 建議改為成交金額（張數 × 收盤價）
all_stocks.sort(key=lambda x: x["volume"] * x["close"], reverse=True)
```

成交金額才是真正可比的流動性指標，NT$50 股票和 NT$500 股票的張數完全不能直接比較。

**改動二：加入成交金額下限（排除流動性不足標的）**

```python
# 成交金額低於 1 億不列入（volume 單位為張，1張=1000股）
if volume * close * 1000 < 100_000_000:
    continue
```

**改動三：加入股價下限（排除低價雜股）**

```python
# 股價低於 $20 不列入（低價股品質差、容易被主力操控）
if close < 20:
    continue
```

#### 整合後的篩選邏輯

```
全市場 TWSE 上市股票
  → 排除 ETF / 非普通股（已有）
  → 排除處置 / 警示股（已有）
  → 排除股價 < $20（新增）
  → 排除成交金額 < 1 億（新增）
  → 依成交金額排序（改動）
  → 取前 N（50 / 100 / 200）
```

#### 請 Codex 一起討論

1. **成交金額門檻 1 億是否合理？** 台灣股市日均成交金額約 2,000–4,000 億，前 200 大約從 10 億以上開始，1 億可能偏低。若要更精準建議 **3 億**，Codex 請評估。

2. **股價下限 $20 是否合理？** 或應改為 **$30** 以排除更多低品質標的？

3. **是否應加上市值下限？** 例如排除市值小於 NT$50 億的公司，避免流動性不穩定的小型股。Codex 若能從 `TaiwanStockInfo` 取得股本或市值，可評估是否可行。

4. **是否考慮加入「近20日均量」門檻？** 例如近 20 日日均成交量 > 500 張，確保今天的量縮不是因為本來就冷門。

#### 建議 Codex 執行優先順序

| 優先 | 項目 | 影響檔案 |
|------|------|---------|
| 🔴 高 | 改為成交金額排序 | `main.py` |
| 🔴 高 | 加入股價 < $20 排除 | `main.py` |
| 🟡 中 | 加入成交金額下限（門檻待討論） | `main.py` |
| 🟢 低 | 評估是否加市值 / 均量門檻 | `main.py` |

完成後請執行 `python -m py_compile main.py` 並更新本文件。

---

## 歷史交接紀錄

### 2026-04-27 至 2026-04-28 已完成整理

#### 已完成主線
- 建立 `AI交接報告.md` 作為 Codex / Claude 共用交接入口。
- 全專案時間來源逐步改為台灣時間 `tw_now()`，前端顯示也同步調整。
- 即時資金雷達完成 Discord 狀態、設定保存、盤中推播與測試 endpoint。
- 籌碼分析頁修正當沖量 / 當沖率錯誤，補周轉率、借券賣，並移除容易 timeout 的 TWSE T86 前置串行查詢。
- ABC 掃描完成第一階段升級：融資性質標籤、`240扣低`、`扣大量`，並排除 ETF / 非普通股。
- 隔日沖候選觀察完成第一版與多輪強化：多頭回檔條件、K棒紅黑、收盤位置、昨日低點、10MA 不下彎、法人成本輔助標籤、ETF 排除、處置 / 警示股排除。
- 盤中監測完成第一版：`假跌破回站`、`守住昨低`、`確認破低`、`跳空破低`、`處置警示`，Discord 文案明確標示行動與停損，並加上零股不適用提醒。
- 新增 `/pullback_monitor/test_discord` 測試四種隔日沖推播文案。
- 新增 `/pullback_monitor/discord_on`、`/pullback_monitor/discord_off` 與前端推播開關。

#### 已完成驗證
- 多次執行 `python -m py_compile main.py` 通過。
- 多次抽取 `index.html` / `ABC選股掃描.html` script 後執行 `node --check` 通過。
- 使用者已測試隔日沖相關功能並回報功能正常。

#### 已解決且不再列為最新待辦
- 登入失敗問題。
- 當沖率異常放大。
- 籌碼分析載入逾時的主要串行瓶頸。
- 盤中監測區塊看不到。
- 非盤中誤顯示買點 / 破低訊號。
- ETF 進入法人籌碼掃描。
- 零股測試未提醒無法當沖。
- Discord 推播無法單獨關閉。
- 處置 / 警示股進入隔日沖候選的主要防呆。

---

### 範本

#### 日期
- YYYY-MM-DD

#### 本次重點
- 修改了什麼
- 發現了什麼

#### 影響檔案
- `main.py`
- `index.html`

#### 驗證結果
- `python -m py_compile main.py` 通過
- 前端 JS `node --check` 通過

#### 未解決事項
- 尚未做整合測試
- 某 API 在特定環境 timeout
