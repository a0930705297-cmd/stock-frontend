import httpx
import requests
import warnings
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
import yfinance as yf
import asyncio

warnings.filterwarnings("ignore")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 所有敏感資訊從環境變數讀取，不寫死在程式碼裡 ──
FINMIND_TOKEN     = os.environ.get("FINMIND_TOKEN", "")
FUGLE_API_KEY     = os.environ.get("FUGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
FUGLE_BASE        = "https://api.fugle.tw/marketdata/v1.0/stock"
API_TOKEN         = os.environ.get("API_TOKEN", "0921")
DISCORD_WEBHOOK   = os.environ.get("DISCORD_WEBHOOK", "")
TW_TZ             = timezone(timedelta(hours=8))


# 分析結果快取
analysis_cache = {}
CACHE_MINUTES = 30

def verify_token(x_token: str):
    if x_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

def twse_get(url):
    try:
        r = requests.get(url, verify=False, timeout=20,
                         headers={"User-Agent": "Mozilla/5.0"})
        return r.json()
    except Exception:
        return None

def finmind_get(dataset, symbol, start_date, end_date):
    url = (
        f"https://api.finmindtrade.com/api/v4/data"
        f"?dataset={dataset}&data_id={symbol}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&token={FINMIND_TOKEN}"
    )
    data = twse_get(url)
    if not data or data.get("msg") != "success":
        return []
    return data.get("data", [])

def parse_int(s):
    try:
        return int(str(s).replace(",", "").replace(" ", "").strip())
    except Exception:
        return 0

def tw_now():
    return datetime.now(TW_TZ)

INDUSTRY_THEME = {
    "半導體業":         ["半導體", "AI"],
    "電腦及週邊設備業": ["伺服器", "AI"],
    "其他電子業":       ["電子零組件"],
    "光電業":           ["光電", "面板"],
    "通信網路業":       ["通信網路"],
    "電子零組件業":     ["電子零組件"],
    "電子通路業":       ["電子通路"],
    "資訊服務業":       ["資訊服務"],
    "航運業":           ["航運"],
    "金融業":           ["金融"],
    "生技醫療業":       ["生技醫療"],
    "電機機械":         ["電機"],
    "汽車工業":         ["電動車"],
    "鋼鐵工業":         ["鋼鐵"],
    "建材營造業":       ["營建"],
    "油電燃氣業":       ["油電燃氣"],
    "觀光餐旅業":       ["觀光"],
    "貿易百貨業":       ["貿易百貨"],
    "化學工業":         ["化學"],
    "塑膠工業":         ["塑膠"],
    "紡織纖維":         ["紡織"],
    "食品工業":         ["食品"],
    "造紙工業":         ["造紙"],
    "橡膠工業":         ["橡膠"],
    "玻璃陶瓷":         ["玻璃"],
    "水泥工業":         ["水泥"],
}

STOCK_EXTRA_THEME = {
    "2330": ["CoWoS", "先進封裝", "AI"],
    "2454": ["IC設計", "AI"],
    "2379": ["載板"],
    "3711": ["散熱", "AI伺服器"],
    "6669": ["散熱", "AI伺服器"],
    "2367": ["PCB", "載板"],
    "3034": ["載板"],
    "8150": ["載板"],
    "3037": ["載板"],
    "2301": ["PCB"],
    "2313": ["PCB"],
    "3044": ["PCB"],
    "2498": ["記憶體"],
    "5347": ["記憶體"],
    "4967": ["銅箔基板"],
    "8046": ["銅箔基板"],
    "6274": ["銅箔基板"],
    "6213": ["銅箔基板"],
    "3189": ["散熱"],
    "6230": ["散熱"],
    "2049": ["散熱"],
    "2383": ["HBM", "記憶體"],
    "3008": ["光學"],
    "2382": ["伺服器", "AI伺服器"],
    "2317": ["伺服器", "AI伺服器"],
    "2357": ["伺服器", "AI伺服器"],
    "3481": ["面板"],
    "2395": ["散熱"],
    "2376": ["伺服器", "AI伺服器"],
    "2408": ["面板"],
    "3706": ["AI伺服器", "散熱"],
    "6547": ["AI", "IC設計"],
    "2303": ["半導體"],
    "2344": ["記憶體"],
    "3443": ["散熱"],
    "6770": ["半導體"],
    "2337": ["記憶體"],
    "2615": ["航運"],
    "2603": ["航運"],
    "2609": ["航運"],
    "2610": ["航運"],
    "2618": ["航運"],
    "2886": ["金融"],
    "2881": ["金融"],
    "2882": ["金融"],
    "2884": ["金融"],
    "2891": ["金融"],
    "1301": ["塑膠", "化學"],
    "1303": ["塑膠", "化學"],
    "1326": ["塑膠", "化學"],
    "2002": ["鋼鐵"],
    "2006": ["鋼鐵"],
    "3491": ["太空衛星", "通信網路"],
    "7717": ["太空衛星", "通信網路"],
    "2313": ["太空衛星", "PCB"],
    "2383": ["太空衛星", "銅箔基板"],
    "3550": ["太空衛星", "PCB"],
    "6285": ["太空衛星", "通信網路"],
    "5388": ["太空衛星", "通信網路"],
    "2458": ["太空衛星", "半導體"],
    "6443": ["太空衛星"],
    "5483": ["太空衛星"],
    "2412": ["太空衛星", "通信網路"],
    "1303": ["玻纖布", "銅箔基板"],
    "1802": ["玻纖布"],
    "1815": ["玻纖布"],
    "5340": ["玻纖布"],
    "4924": ["玻纖布"],
    "4438": ["玻纖布"],
    "8046": ["玻纖布", "銅箔基板"],
}

THEME_US_STOCKS = {
    "半導體":     [("NVDA", "輝達"), ("AMD", "超微"), ("SOXX", "費半ETF"), ("AMAT", "應用材料"), ("KLAC", "科磊")],
    "AI":         [("NVDA", "輝達"), ("AMD", "超微"), ("SOXX", "費半ETF"), ("MSFT", "微軟"), ("GOOGL", "谷歌")],
    "CoWoS":      [("NVDA", "輝達"), ("AMAT", "應用材料"), ("KLAC", "科磊"), ("LRCX", "科林研發")],
    "先進封裝":   [("NVDA", "輝達"), ("AMAT", "應用材料"), ("KLAC", "科磊"), ("LRCX", "科林研發")],
    "IC設計":     [("NVDA", "輝達"), ("AMD", "超微"), ("QCOM", "高通"), ("AVGO", "博通")],
    "載板":       [("AMAT", "應用材料"), ("KLAC", "科磊"), ("LRCX", "科林研發"), ("TER", "泰瑞達")],
    "PCB":        [("AMAT", "應用材料"), ("TTM", "TTM科技"), ("KOPN", "Kopin")],
    "銅箔基板":   [("FCX", "自由港銅礦"), ("COPX", "銅礦ETF"), ("HG=F", "銅期貨"), ("AA", "美國鋁業")],
    "記憶體":     [("MU", "美光"), ("SNDK", "閃迪"), ("WDC", "威騰")],
    "HBM":        [("MU", "美光"), ("SNDK", "閃迪"), ("NVDA", "輝達")],
    "伺服器":     [("NVDA", "輝達"), ("DELL", "戴爾"), ("HPE", "慧與科技"), ("SMCI", "超微電腦")],
    "AI伺服器":   [("NVDA", "輝達"), ("DELL", "戴爾"), ("SMCI", "超微電腦"), ("AVGO", "博通")],
    "散熱":       [("NVDA", "輝達"), ("DELL", "戴爾"), ("SMCI", "超微電腦"), ("VRT", "維谛技術")],
    "光電":       [("OLED", "Universal Display"), ("AAPL", "蘋果"), ("VIZIO", "Vizio")],
    "面板":       [("OLED", "Universal Display"), ("AAPL", "蘋果"), ("LGD", "樂金顯示")],
    "通信網路":   [("QCOM", "高通"), ("CSCO", "思科"), ("ERIC", "愛立信"), ("NOK", "諾基亞")],
    "航運":       [("ZIM", "以星航運"), ("SBLK", "星散航運"), ("MATX", "馬士基"), ("DAC", "達飛")],
    "金融":       [("XLF", "金融ETF"), ("JPM", "摩根大通"), ("GS", "高盛"), ("BAC", "美國銀行")],
    "生技醫療":   [("XBI", "生技ETF"), ("JNJ", "嬌生"), ("PFE", "輝瑞"), ("ABBV", "艾伯維")],
    "電動車":     [("TSLA", "特斯拉"), ("GM", "通用汽車"), ("F", "福特"), ("RIVN", "Rivian")],
    "電子零組件": [("AMAT", "應用材料"), ("TXN", "德州儀器"), ("AVGO", "博通"), ("MCHP", "微晶片科技")],
    "光學":       [("AAPL", "蘋果"), ("VIAV", "Viavi Solutions")],
    "資訊服務":   [("MSFT", "微軟"), ("GOOGL", "谷歌"), ("META", "Meta"), ("ORCL", "甲骨文")],
    "電子通路":   [("AVT", "安富利"), ("ARW", "艾睿電子")],
    "鋼鐵":       [("NUE", "紐柯鋼鐵"), ("X", "美國鋼鐵"), ("CLF", "克里夫蘭鋼鐵")],
    "化學":       [("LYB", "利安德巴塞爾"), ("DD", "杜邦"), ("DOW", "陶氏化學")],
    "塑膠":       [("LYB", "利安德巴塞爾"), ("DOW", "陶氏化學")],
    "油電燃氣":   [("XOM", "埃克森美孚"), ("CVX", "雪佛龍"), ("COP", "康菲石油")],
    "航運":       [("ZIM", "以星航運"), ("SBLK", "星散航運"), ("DAC", "達飛"), ("MATX", "馬士基")],
    "電機":       [("ETN", "伊頓"), ("EMR", "艾默生"), ("ROK", "洛克威爾")],
    "營建":       [("DHI", "霍頓房屋"), ("LEN", "萊納房屋"), ("PHM", "普爾特房屋")],
    "食品":       [("MCD", "麥當勞"), ("KO", "可口可樂"), ("PEP", "百事可樂")],
    "紡織":       [("NKE", "耐吉"), ("VFC", "VF集團")],
    "觀光":       [("MAR", "萬豪酒店"), ("HLT", "希爾頓"), ("DAL", "達美航空")],
    "貿易百貨":   [("WMT", "沃爾瑪"), ("COST", "好市多"), ("AMZN", "亞馬遜")],
    "太空衛星":   [("RKLB", "火箭實驗室"), ("ASTS", "AST SpaceMobile"), ("MNTS", "Momentus"), ("SPCE", "維珍銀河"), ("VSAT", "Viasat")],
    "玻纖布": [("AMAT", "應用材料"), ("GLW", "康寧"), ("OC", "歐文斯康寧")],
}

@app.get("/history/{symbol}")
async def get_history(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    url = f"{FUGLE_BASE}/historical/candles/{symbol}?timeframe=D&sort=asc"
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.get(url, headers={"X-API-KEY": FUGLE_API_KEY})
                return res.json()
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            if attempt == 2:
                return {"error": str(e), "data": []}
            continue

@app.get("/ticker/{symbol}")
async def get_ticker(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    url = f"{FUGLE_BASE}/intraday/ticker/{symbol}"
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(url, headers={"X-API-KEY": FUGLE_API_KEY})
                return res.json()
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            if attempt == 2:
                return {"error": str(e), "name": symbol}
            continue

@app.get("/foreign/{symbol}")
async def get_foreign(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    today = tw_now()
    start = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    rows = finmind_get("TaiwanStockInstitutionalInvestorsBuySell", symbol, start, end)
    result = []
    for row in rows:
        if row.get("name") != "Foreign_Investor":
            continue
        buy = max(int(row.get("buy", 0)), 0) // 1000
        sell = max(int(row.get("sell", 0)), 0) // 1000
        result.append({
            "date": row["date"].replace("-", ""),
            "buy": buy,
            "sell": sell,
            "net": buy - sell
        })
    result.sort(key=lambda x: x["date"])
    return {"data": result}

@app.get("/invest_trust/{symbol}")
async def get_invest_trust(symbol: str, x_token: str = Header(default=None)):
    """投信買賣超，格式與 /foreign 相同，供前端計算投信加權成本"""
    verify_token(x_token)
    today = tw_now()
    start = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    rows = finmind_get("TaiwanStockInstitutionalInvestorsBuySell", symbol, start, end)
    result = []
    for row in rows:
        if row.get("name") != "Investment_Trust":
            continue
        buy = max(int(row.get("buy", 0)), 0) // 1000
        sell = max(int(row.get("sell", 0)), 0) // 1000
        result.append({
            "date": row["date"].replace("-", ""),
            "buy": buy,
            "sell": sell,
            "net": buy - sell
        })
    result.sort(key=lambda x: x["date"])
    return {"data": result}

@app.get("/margin/{symbol}")
async def get_margin(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    today = tw_now()
    start = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    rows = finmind_get("TaiwanStockMarginPurchaseShortSale", symbol, start, end)
    result = []
    for row in rows:
        buy = int(row.get("MarginPurchaseBuy", 0))
        sell = int(row.get("MarginPurchaseSell", 0))
        balance = int(row.get("MarginPurchaseTodayBalance", 0))
        result.append({
            "date": row["date"].replace("-", ""),
            "buy": buy,
            "sell": sell,
            "balance": balance
        })
    result.sort(key=lambda x: x["date"])
    return {"data": result}

@app.get("/price/{symbol}")
async def get_price(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    today = tw_now()
    start = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    rows = finmind_get("TaiwanStockPrice", symbol, start, end)
    result = {}
    for row in rows:
        date_key = row["date"].replace("-", "")
        close  = float(row.get("close",  0))
        high   = float(row.get("max",    close))   # FinMind 高價欄位
        low    = float(row.get("min",    close))   # FinMind 低價欄位
        volume = int(float(row.get("Trading_Volume", 0)))
        result[date_key] = {
            "close":  close,
            "avg":    close,
            "max":    high,
            "min":    low,
            "volume": volume
        }
    return {"data": result}

# 美股產業 -> 台股主題對應表
US_SECTOR_THEME = {
    "Semiconductors":                    ["半導體", "AI"],
    "Semiconductor Equipment & Materials": ["載板", "先進封裝"],
    "Electronic Components":             ["電子零組件"],
    "Computer Hardware":                 ["伺服器", "AI伺服器"],
    "Information Technology Services":   ["資訊服務"],
    "Software - Application":            ["AI", "資訊服務"],
    "Software - Infrastructure":         ["AI", "資訊服務"],
    "Communication Equipment":           ["通信網路"],
    "Consumer Electronics":              ["電子零組件"],
    "Electronic Gaming & Multimedia":    ["光電"],
    "Displays":                          ["面板", "光電"],
    "Solar":                             ["油電燃氣"],
    "Specialty Chemicals":               ["化學", "銅箔基板"],
    "Copper":                            ["銅箔基板"],
    "Gold":                              ["鋼鐵"],
    "Steel":                             ["鋼鐵"],
    "Marine Shipping":                   ["航運"],
    "Air Freight & Logistics":           ["航運"],
    "Banks - Diversified":               ["金融"],
    "Financial Services":                ["金融"],
    "Insurance":                         ["金融"],
    "Biotechnology":                     ["生技醫療"],
    "Medical Devices":                   ["生技醫療"],
    "Drug Manufacturers":                ["生技醫療"],
    "Auto Manufacturers":                ["電動車"],
    "Auto Parts":                        ["電動車"],
    "Oil & Gas Integrated":              ["油電燃氣"],
    "Oil & Gas E&P":                     ["油電燃氣"],
    "Printed Circuit Boards":            ["PCB", "載板"],
    "Electronic Distribution":           ["電子通路"],
    "Data Storage":                      ["記憶體", "AI伺服器"],
    "Memory Chips":                      ["記憶體", "HBM"],
    "Computer Systems":                  ["伺服器", "AI伺服器"],
    "Thermal Management":                ["散熱"],
}

@app.get("/theme/{symbol}")
async def get_theme(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    try:
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo&data_id={symbol}"
        data = twse_get(url)
        industry = ""
        if data and data.get("msg") == "success" and data.get("data"):
            industry = data["data"][0].get("industry_category", "")

        themes = list(INDUSTRY_THEME.get(industry, []))
        extra = STOCK_EXTRA_THEME.get(symbol, [])
        for t in extra:
            if t not in themes:
                themes.append(t)

        us_stocks = {}
        for theme in themes:
            for ticker, name in THEME_US_STOCKS.get(theme, []):
                if ticker not in us_stocks:
                    us_stocks[ticker] = name

        return {
            "industry": industry,
            "themes": themes,
            "us_stocks": [{"ticker": k, "name": v} for k, v in us_stocks.items()]
        }
    except Exception as e:
        return {
            "industry": "",
            "themes": [],
            "us_stocks": []
        }

        # 用 US_SECTOR_THEME 對應主題找額外美股
        for ticker in reference_tickers:
            if ticker in us_stocks_dict:
                continue
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(get_ticker_info, ticker)
                    t, info = future.result(timeout=3)
                    if info:
                        ind = getattr(info, 'industry', '') or ''
                        matched_themes = US_SECTOR_THEME.get(ind, [])
                        for mt in matched_themes:
                            if mt in themes:
                                name = ticker
                                extra_us[ticker] = name
                                break
            except Exception:
                continue

    except Exception:
        pass

@app.get("/us_price/{ticker}")
async def get_us_price(ticker: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=10d"
    try:
        r = requests.get(url, verify=False, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        prices = []
        for ts, close in zip(timestamps, closes):
            if close is None:
                continue
            date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            prices.append({"date": date, "close": round(close, 2)})
        prices = prices[-5:]
        latest = prices[-1] if prices else {}
        prev = prices[-2] if len(prices) >= 2 else {}
        change = round(latest.get("close", 0) - prev.get("close", 0), 2) if prev else 0
        change_pct = round(change / prev.get("close", 1) * 100, 2) if prev else 0
        return {
            "ticker": ticker,
            "latest_date": latest.get("date", ""),
            "latest_close": latest.get("close", 0),
            "prev_close": prev.get("close", 0),
            "change": change,
            "change_pct": change_pct,
            "prices": prices
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

@app.get("/news")
async def get_news(x_token: str = Header(default=None)):
    verify_token(x_token)
    url = "https://news.google.com/rss/search?q=%E6%AC%8A%E8%AD%89+site:money.udn.com&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=10)
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        result = []
        for item in items[:20]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            result.append({"title": title, "link": link, "pub_date": pub_date})
        return {"data": result}
    except Exception as e:
        return {"data": [], "error": str(e)}

@app.post("/analyze")
async def analyze(body: dict, x_token: str = Header(default=None)):
    verify_token(x_token)

    stock_code = body.get("stock_code", "")
    current_price = body.get("current_price", 0)

    # 檢查快取
    cache_key = f"{stock_code}_{current_price}"
    if cache_key in analysis_cache:
        cached = analysis_cache[cache_key]
        elapsed = (tw_now() - cached["time"]).total_seconds() / 60
        if elapsed < CACHE_MINUTES:
            print(f"快取命中：{cache_key}，距上次 {elapsed:.1f} 分鐘")
            return {"analysis": cached["text"], "cached": True}

    stock_name = body.get("stock_name", "")
    industry = body.get("industry", "")
    themes = body.get("themes", [])
    foreign_cost = body.get("foreign_cost", 0)
    margin_cost = body.get("margin_cost", 0)
    foreign_verdict = body.get("foreign_verdict", "")
    margin_verdict = body.get("margin_verdict", "")
    foreign_accumulate = body.get("foreign_accumulate", "")
    trend = body.get("trend", "")
    us_stocks = body.get("us_stocks", [])

    prompt = f"""你是一位專業的台股分析師，請根據以下資料對這支股票提供簡潔的分析建議。

股票：{stock_name}（{stock_code}）
產業：{industry}
主題：{', '.join(themes)}
現價：{current_price} 元

外資成本：{foreign_cost} 元
外資位階：{foreign_verdict}
融資成本：{margin_cost} 元
融資位階：{margin_verdict}

外資近期動向：{foreign_accumulate}
股價線型：{trend}

對應美股昨日表現：
{chr(10).join([f"- {s['ticker']} {s['name']}：{'+' if s['change_pct'] >= 0 else ''}{s['change_pct']}%" for s in us_stocks])}

請提供：
1. 目前位階總結（2-3句）
2. 法人籌碼觀察（2-3句）
3. 美股連動分析（1-2句）
4. 操作建議（2-3句）

注意：
- 用繁體中文回答
- 語氣專業但口語化
- 不要用條列式，用段落方式呈現
- 最後加一句免責聲明
- 總字數控制在200字以內"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            verify=False,
            timeout=30
        )
        data = r.json()
        if "content" not in data:
            return {"analysis": f"API錯誤：{data}", "cached": False}
        text = data["content"][0]["text"]

        # 存入快取
        analysis_cache[cache_key] = {
            "text": text,
            "time": tw_now()
        }
        print(f"新分析已快取：{cache_key}")

        return {"analysis": text, "cached": False}
    except Exception as e:
        return {"analysis": f"分析生成失敗：{str(e)}", "cached": False}

@app.get("/revenue/{symbol}")
async def get_revenue(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    today = tw_now()
    start = (today - timedelta(days=760)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    rows = finmind_get("TaiwanStockMonthRevenue", symbol, start, end)

    result = []
    for row in rows:
        revenue = int(row.get("revenue", 0))
        result.append({
            "date": row["date"],
            "year": int(row.get("revenue_year", 0)),
            "month": int(row.get("revenue_month", 0)),
            "revenue": revenue
        })

    result.sort(key=lambda x: x["date"])

    # 計算月增率和年增率
    for i, row in enumerate(result):
        prev_month = result[i-1]["revenue"] if i > 0 else 0
        prev_year = result[i-12]["revenue"] if i >= 12 else 0
        row["mom"] = round((row["revenue"] - prev_month) / prev_month * 100, 1) if prev_month > 0 else 0
        row["yoy"] = round((row["revenue"] - prev_year) / prev_year * 100, 1) if prev_year > 0 else 0

    return {"data": result[-15:]}
@app.get("/market_volume")
async def get_market_volume(x_token: str = Header(default=None)):
    verify_token(x_token)
    today = tw_now()
    for i in range(5):
        try_date = (today - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX20?date={try_date}&response=json"
        data = twse_get(url)
        if data and data.get("stat") == "OK" and data.get("data"):
            result = []
            for row in data["data"][:100]:
                try:
                    code = str(row[1]).strip()
                    name = str(row[2]).strip()
                    close = float(str(row[8]).replace(",", "")) if row[8] else 0
                    volume = int(str(row[3]).replace(",", "")) if row[3] else 0
                    result.append({
                        "code": code,
                        "name": name,
                        "close": close,
                        "volume": volume
                    })
                except Exception:
                    continue
            return {"data": result, "date": try_date}
    return {"data": [], "date": ""}

@app.get("/industry_stocks/{industry}")
async def get_industry_stocks(industry: str, x_token: str = Header(default=None)):
    verify_token(x_token)

    # 先檢查是否為自訂主題
    if industry in CUSTOM_THEME_STOCKS:
        return {"data": CUSTOM_THEME_STOCKS[industry]}

    # 否則從 FinMind 抓官方產業
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo&start_date=2024-01-01"
    data = twse_get(url)
    if not data or data.get("msg") != "success":
        return {"data": []}
    rows = [x for x in data.get("data", [])
            if x.get("industry_category") == industry
            and x.get("type") in ["twse", "tpex"]]
    return {"data": [{"code": x["stock_id"], "name": x["stock_name"]} for x in rows]}

CUSTOM_THEME_STOCKS = {
    "太空衛星": [
        {"code": "3491", "name": "昇達科"},
        {"code": "7717", "name": "萊德光電"},
        {"code": "2313", "name": "華通"},
        {"code": "2383", "name": "台光電"},
        {"code": "6285", "name": "啟碁"},
        {"code": "2458", "name": "義隆"},
        {"code": "5388", "name": "中磊"},
        {"code": "6443", "name": "元晶"},
        {"code": "5483", "name": "中美晶"},
        {"code": "2412", "name": "中華電"},
    ],
    "玻纖布": [
        {"code": "1303", "name": "南亞"},
        {"code": "1802", "name": "台玻"},
        {"code": "1815", "name": "富喬"},
        {"code": "5340", "name": "建榮"},
        {"code": "4924", "name": "德宏"},
        {"code": "4438", "name": "廣越"},
        {"code": "8046", "name": "南電"},
    ],
    "銅箔基板": [
        {"code": "2383", "name": "台光電"},
        {"code": "1303", "name": "南亞"},
        {"code": "6274", "name": "台燿"},
        {"code": "1717", "name": "長興"},
        {"code": "6213", "name": "聯茂"},
        {"code": "8039", "name": "台虹"},
        {"code": "5498", "name": "凱崴"},
        {"code": "1612", "name": "宏泰"},
        {"code": "6672", "name": "騰輝電子-KY"},
        {"code": "4939", "name": "亞電"},
        {"code": "3354", "name": "律勝"},
        {"code": "8291", "name": "尚茂"},
    ],
    "被動元件": [
        {"code": "6224", "name": "聚鼎"},
        {"code": "6204", "name": "艾華"},
        {"code": "2472", "name": "立隆電"},
        {"code": "6127", "name": "九豪"},
        {"code": "3026", "name": "禾伸堂"},
        {"code": "8042", "name": "金山電"},
        {"code": "2492", "name": "華新科"},
        {"code": "2428", "name": "興勤"},
        {"code": "6597", "name": "立誠"},
        {"code": "8043", "name": "蜜望實"},
        {"code": "6834", "name": "天二科技"},
        {"code": "3090", "name": "日電貿"},
        {"code": "2327", "name": "國巨"},
        {"code": "6449", "name": "鈺邦"},
        {"code": "2478", "name": "大毅"},
        {"code": "3357", "name": "臺慶科"},
        {"code": "6173", "name": "信昌電"},
        {"code": "6432", "name": "今展科"},
        {"code": "3191", "name": "雲嘉南"},
        {"code": "3624", "name": "光頡"},
        {"code": "8121", "name": "越峰"},
        {"code": "6284", "name": "佳邦"},
        {"code": "5228", "name": "鈺鎧"},
        {"code": "6207", "name": "雷科"},
        {"code": "2375", "name": "凱美"},
        {"code": "4760", "name": "勤凱"},
        {"code": "6155", "name": "鈞寶"},
        {"code": "6175", "name": "立敦"},
        {"code": "3236", "name": "千如"},
        {"code": "5328", "name": "華容"},
        {"code": "3117", "name": "年程"},
        {"code": "6862", "name": "三集瑞-KY"},
    ],
}
@app.post("/scan")
async def scan(body: dict, x_token: str = Header(default=None)):
    verify_token(x_token)
    codes = body.get("codes", [])
    today = tw_now()
    start = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    # 補抓沒有收盤價的股票現價
    for item in codes:
        if item.get("close", 0) == 0:
            try:
                price_rows = finmind_get("TaiwanStockPrice", item["code"],
                    (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    today.strftime("%Y-%m-%d"))
                if price_rows:
                    item["close"] = float(price_rows[-1].get("close", 0))
            except Exception:
                pass

    results = []
    for item in codes[:10]:
        code = item["code"]
        name = item["name"]
        close = item.get("close", 0)
        try:
            foreign_rows = finmind_get(
                "TaiwanStockInstitutionalInvestorsBuySell", code, start, end)
            price_rows = finmind_get("TaiwanStockPrice", code, start, end)

            prices = {}
            for row in price_rows:
                date_key = row["date"].replace("-", "")
                c = float(row.get("close", 0))
                prices[date_key] = {"close": c, "avg": c}

            foreign = []
            for row in foreign_rows:
                if row.get("name") != "Foreign_Investor":
                    continue
                buy = max(int(row.get("buy", 0)), 0) // 1000
                sell = max(int(row.get("sell", 0)), 0) // 1000
                foreign.append({
                    "date": row["date"].replace("-", ""),
                    "buy": buy, "sell": sell
                })

            holdings, total_cost = 0, 0
            for d in foreign:
                price = prices.get(d["date"], {}).get("close", 0)
                if not price:
                    continue
                if d["buy"] > 0:
                    total_cost += d["buy"] * 1000 * price
                    holdings += d["buy"] * 1000
                if d["sell"] > 0 and holdings > 0:
                    s = min(d["sell"] * 1000, holdings)
                    total_cost -= s * (total_cost / holdings)
                    holdings -= s

            f_cost = total_cost / holdings if holdings > 0 else 0
            trigger = f_cost * 1.04
            p1 = f_cost * 1.2
            p2 = f_cost * 1.4
            p4 = f_cost * 1.7

            if f_cost <= 0:
                zone = "無法計算"
                css = "neutral"
            elif close < f_cost:
                zone = "跌破成本"
                css = "neutral"
            elif close < trigger:
                zone = "醞釀期"
                css = "neutral"
            elif close < p1:
                zone = "第一攻擊區"
                css = "good"
            elif close < p2:
                zone = "第二攻擊區"
                css = "ok"
            elif close < p4:
                zone = "極端高位區"
                css = "warning"
            else:
                zone = "韭菜收割區"
                css = "danger"

            results.append({
                "code": code,
                "name": name,
                "close": close,
                "foreign_cost": round(f_cost, 1),
                "trigger": round(trigger, 1),
                "p1": round(p1, 1),
                "zone": zone,
                "css": css
            })
        except Exception as e:
            results.append({
                "code": code, "name": name,
                "close": close, "foreign_cost": 0,
                "trigger": 0, "p1": 0,
                "zone": "計算失敗", "css": "neutral"
            })

    return {"data": results}

@app.post("/technical_scan")
async def technical_scan(body: dict, x_token: str = Header(default=None)):
    verify_token(x_token)
    top_n = body.get("top_n", 100)

    # 抓全市場當日成交資料
    today = tw_now()
    all_stocks = []

    for i in range(5):
        try_date = (today - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY_ALL?response=json&date={try_date}"
        data = twse_get(url)
        if data and data.get("stat") == "OK" and data.get("data"):
            for row in data["data"]:
                try:
                    code = str(row[0]).strip()
                    name = str(row[1]).strip()
                    volume = int(str(row[2]).replace(",", "")) if row[2] else 0
                    close = float(str(row[7]).replace(",", "")) if row[7] else 0
                    if not code.isdigit():
                        continue
                    if volume <= 0 or close <= 0:
                        continue
                    all_stocks.append({
                        "code": code, "name": name,
                        "close": close, "volume": volume
                    })
                except Exception:
                    continue
            break

    if not all_stocks:
        return {"data": [], "error": "無法取得當日成交資料"}

    # 依成交量排序，取前 top_n
    all_stocks.sort(key=lambda x: x["volume"], reverse=True)
    target_stocks = all_stocks[:top_n]

    results = []
    start_date = (today - timedelta(days=120)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    for item in target_stocks:
        code = item["code"]
        name = item["name"]
        close = item["close"]

        try:
            price_rows = finmind_get("TaiwanStockPrice", code, start_date, end_date)
            if len(price_rows) < 60:
                continue

            closes = [float(r.get("close", 0)) for r in price_rows]
            volumes = [int(r.get("Trading_Volume", 0)) for r in price_rows]

            def ma(data, n):
                return sum(data[-n:]) / n if len(data) >= n else 0

            ma5 = ma(closes, 5)
            ma10 = ma(closes, 10)
            ma20 = ma(closes, 20)
            ma60 = ma(closes, 60)

            bullish = ma5 > ma20 > ma60

            obv_list = [0]
            for j in range(1, len(closes)):
                if closes[j] > closes[j-1]:
                    obv_list.append(obv_list[-1] + volumes[j])
                elif closes[j] < closes[j-1]:
                    obv_list.append(obv_list[-1] - volumes[j])
                else:
                    obv_list.append(obv_list[-1])

            obv_recent = obv_list[-20:]
            obv_breakthrough = obv_list[-1] >= max(obv_recent)

            if not (bullish and obv_breakthrough):
                continue

            # 計算外資成本
            foreign_rows = finmind_get(
                "TaiwanStockInstitutionalInvestorsBuySell", code, start_date, end_date)

            price_map = {}
            for row in price_rows:
                date_key = row["date"].replace("-", "")
                price_map[date_key] = float(row.get("close", 0))

            holdings, total_cost = 0, 0
            for d in foreign_rows:
                if d.get("name") != "Foreign_Investor":
                    continue
                date_key = d["date"].replace("-", "")
                price = price_map.get(date_key, 0)
                if not price:
                    continue
                buy = max(int(d.get("buy", 0)), 0) // 1000
                sell = max(int(d.get("sell", 0)), 0) // 1000
                if buy > 0:
                    total_cost += buy * 1000 * price
                    holdings += buy * 1000
                if sell > 0 and holdings > 0:
                    s = min(sell * 1000, holdings)
                    total_cost -= s * (total_cost / holdings)
                    holdings -= s

            f_cost = total_cost / holdings if holdings > 0 else 0

            # 波段密碼計算
            if f_cost > 0:
                p1 = f_cost * 1.04
                p2 = f_cost * 1.2
                p3 = f_cost * 1.4
                p4 = f_cost * 1.7

                if close < f_cost:
                    zone = "跌破成本"
                    zone_css = "neutral"
                elif close < p1:
                    zone = "醞釀期"
                    zone_css = "neutral"
                elif close < p2:
                    zone = "第一攻擊區"
                    zone_css = "good"
                elif close < p3:
                    zone = "第二攻擊區"
                    zone_css = "ok"
                elif close < p4:
                    zone = "極端高位區"
                    zone_css = "warning"
                else:
                    zone = "韭菜收割區"
                    zone_css = "danger"
            else:
                zone = "無法計算"
                zone_css = "neutral"
                f_cost = 0
                p1 = p2 = p3 = p4 = 0

            results.append({
                "code": code,
                "name": name,
                "close": close,
                "ma5": round(ma5, 1),
                "ma10": round(ma10, 1),
                "ma20": round(ma20, 1),
                "ma60": round(ma60, 1),
                "volume": item["volume"],
                "foreign_cost": round(f_cost, 1),
                "trigger": round(p1, 1) if f_cost > 0 else 0,
                "p1": round(p2, 1) if f_cost > 0 else 0,
                "zone": zone,
                "zone_css": zone_css
            })

        except Exception:
            continue

    results.sort(key=lambda x: x["volume"], reverse=True)
    return {"data": results}

def _calc_foreign_cost_from_rows(foreign_rows: list, price_rows: list) -> float:
    price_map = {}
    for row in price_rows:
        try:
            date_key = str(row.get("date", "")).replace("-", "")
            price_map[date_key] = float(row.get("close", 0) or 0)
        except Exception:
            continue

    holdings = 0
    total_cost = 0
    for row in foreign_rows:
        try:
            if row.get("name") != "Foreign_Investor":
                continue
            date_key = str(row.get("date", "")).replace("-", "")
            price = price_map.get(date_key, 0)
            if price <= 0:
                continue
            buy = max(int(float(row.get("buy", 0) or 0)), 0) // 1000
            sell = max(int(float(row.get("sell", 0) or 0)), 0) // 1000
            if buy > 0:
                total_cost += buy * 1000 * price
                holdings += buy * 1000
            if sell > 0 and holdings > 0:
                sold = min(sell * 1000, holdings)
                total_cost -= sold * (total_cost / holdings)
                holdings -= sold
        except Exception:
            continue

    return total_cost / holdings if holdings > 0 else 0

_disposal_cache = {"codes": set(), "ts": 0}

def _fetch_disposal_stocks() -> set:
    """取得 TWSE 處置股 / 警示股清單，快取 30 分鐘。"""
    now_ts = _time.time()
    if _disposal_cache["codes"] and now_ts - _disposal_cache["ts"] < 1800:
        return _disposal_cache["codes"]

    codes = set()
    urls = [
        "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json",
        "https://www.twse.com.tw/rwd/zh/announcement/warning?response=json",
    ]
    for url in urls:
        data = twse_get(url)
        if not data or not data.get("data"):
            continue
        for row in data.get("data", []):
            for cell in row[:4]:
                code = str(cell).strip()
                if code.isdigit() and len(code) == 4 and not code.startswith("0"):
                    codes.add(code)
                    break

    _disposal_cache["codes"] = codes
    _disposal_cache["ts"] = now_ts
    return codes

@app.post("/pullback_scan")
async def pullback_scan(body: dict, x_token: str = Header(default=None)):
    verify_token(x_token)
    top_n = body.get("top_n", 100)

    today = tw_now()
    all_stocks = []
    disposal_codes = _fetch_disposal_stocks()

    for i in range(5):
        try_date = (today - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY_ALL?response=json&date={try_date}"
        data = twse_get(url)
        if data and data.get("stat") == "OK" and data.get("data"):
            for row in data["data"]:
                try:
                    code = str(row[0]).strip()
                    name = str(row[1]).strip()
                    volume = int(str(row[2]).replace(",", "")) if row[2] else 0
                    amount = int(str(row[3]).replace(",", "")) if len(row) > 3 and row[3] else 0
                    close = float(str(row[7]).replace(",", "")) if row[7] else 0
                    if not code.isdigit() or volume <= 0 or close <= 0:
                        continue
                    if code.startswith("0") or len(code) != 4:
                        continue
                    if code in disposal_codes:
                        continue
                    if amount <= 0:
                        amount = int(volume * close)
                    if close < 20 or amount < 100_000_000:
                        continue
                    all_stocks.append({
                        "code": code,
                        "name": name,
                        "close": close,
                        "volume": volume,
                        "amount": amount,
                        "amount_yi": round(amount / 100_000_000, 2),
                    })
                except Exception:
                    continue
            break

    if not all_stocks:
        return {"data": [], "error": "無法取得當日成交資料"}

    all_stocks.sort(key=lambda x: x["amount"], reverse=True)
    target_stocks = all_stocks[:top_n]

    results = []
    start_date = (today - timedelta(days=140)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    def ma_at(values, n, end_idx=None):
        if end_idx is None:
            end_idx = len(values)
        start_idx = end_idx - n
        if start_idx < 0:
            return 0
        return sum(values[start_idx:end_idx]) / n

    for item in target_stocks:
        code = item["code"]
        name = item["name"]
        close = item["close"]

        try:
            price_rows = finmind_get("TaiwanStockPrice", code, start_date, end_date)
            if len(price_rows) < 65:
                continue

            price_rows = sorted(price_rows, key=lambda x: x.get("date", ""))
            closes = [float(r.get("close", 0)) for r in price_rows]
            volumes = [int(r.get("Trading_Volume", 0)) for r in price_rows]
            if len(closes) < 65 or closes[-1] <= 0:
                continue

            ma5 = ma_at(closes, 5)
            ma10 = ma_at(closes, 10)
            ma20 = ma_at(closes, 20)
            ma60 = ma_at(closes, 60)
            prev_ma5 = ma_at(closes, 5, len(closes) - 1)
            prev_ma10 = ma_at(closes, 10, len(closes) - 1)
            prev_ma20 = ma_at(closes, 20, len(closes) - 1)
            prev_ma60 = ma_at(closes, 60, len(closes) - 1)
            avg_vol20 = ma_at(volumes, 20)
            avg_amount20 = sum(
                volumes[i] * closes[i] for i in range(len(closes) - 20, len(closes))
            ) / 20
            if avg_amount20 < 300_000_000 or avg_vol20 < 3_000_000:
                continue
            prev_row = price_rows[-2]
            today_open = float(price_rows[-1].get("open", closes[-1]) or closes[-1])
            today_high = float(price_rows[-1].get("max", closes[-1]) or closes[-1])
            today_low = float(price_rows[-1].get("min", closes[-1]) or closes[-1])
            today_close = closes[-1]
            today_volume = volumes[-1]
            prev_low = float(prev_row.get("min", 0) or 0)
            day_range = today_high - today_low
            close_pos = round((today_close - today_low) / day_range, 2) if day_range > 0 else 0.5
            close_pos = max(0, min(close_pos, 1))
            candle = "紅K" if today_close >= today_open else "黑K"

            trend_ok = (
                ma20 > ma60
                and ma20 >= prev_ma20
                and ma10 >= prev_ma10
                and ma60 >= prev_ma60
                and today_close > ma60
            )
            cross_down = prev_ma5 >= prev_ma10 and ma5 < ma10
            heavy_black = today_close < today_open and today_volume > avg_vol20
            controlled_pullback = (
                (avg_vol20 <= 0 or today_volume <= avg_vol20)
                and not heavy_black
            )
            not_breakdown = today_close >= ma20 * 0.96

            if not (trend_ok and cross_down and controlled_pullback and not_breakdown):
                continue

            ma20_gap_pct = round((today_close - ma20) / ma20 * 100, 2) if ma20 > 0 else 0
            vol_ratio = round(today_volume / avg_vol20, 2) if avg_vol20 > 0 else 0
            foreign_cost = 0
            foreign_cost_gap_pct = None
            foreign_cost_label = ""
            foreign_cost_css = ""

            try:
                foreign_rows = finmind_get(
                    "TaiwanStockInstitutionalInvestorsBuySell", code, start_date, end_date
                )
                foreign_cost = _calc_foreign_cost_from_rows(foreign_rows, price_rows)
                if foreign_cost > 0:
                    foreign_cost_gap_pct = round((today_close - foreign_cost) / foreign_cost * 100, 2)
                    if abs(foreign_cost_gap_pct) <= 5:
                        foreign_cost_label = "法人成本支撐"
                        foreign_cost_css = "good"
                    elif -10 <= foreign_cost_gap_pct < -5:
                        foreign_cost_label = "成本破位"
                        foreign_cost_css = "warning"
                    elif foreign_cost_gap_pct < -10:
                        foreign_cost_label = "成本深破"
                        foreign_cost_css = "danger"
            except Exception:
                foreign_cost = 0

            if abs(ma20_gap_pct) <= 2:
                signal = "貼近20MA"
                signal_css = "good"
                score = 3
            elif ma20_gap_pct > 2:
                signal = "等回測"
                signal_css = "warning"
                score = 2
            else:
                signal = "弱觀察"
                signal_css = "neutral"
                score = 1

            if candle == "紅K":
                score += 1
            if close_pos < 0.3:
                score -= 1
            score = max(0, score)

            results.append({
                "code": code,
                "name": name,
                "close": close,
                "ma5": round(ma5, 1),
                "ma10": round(ma10, 1),
                "ma20": round(ma20, 1),
                "ma60": round(ma60, 1),
                "ma20_gap_pct": ma20_gap_pct,
                "vol_ratio": vol_ratio,
                "candle": candle,
                "close_pos": close_pos,
                "close_pos_pct": round(close_pos * 100),
                "prev_low": round(prev_low, 2),
                "foreign_cost": round(foreign_cost, 1) if foreign_cost > 0 else 0,
                "foreign_cost_gap_pct": foreign_cost_gap_pct,
                "foreign_cost_label": foreign_cost_label,
                "foreign_cost_css": foreign_cost_css,
                "volume": item["volume"],
                "amount": item["amount"],
                "amount_yi": item["amount_yi"],
                "avg_volume20_lots": round(avg_vol20 / 1000),
                "avg_amount20_yi": round(avg_amount20 / 100_000_000, 2),
                "signal": signal,
                "signal_css": signal_css,
                "score": score
            })

        except Exception:
            continue

    results.sort(key=lambda x: (x["score"], -abs(x["ma20_gap_pct"])), reverse=True)
    return {"data": results}

# ── 共用工具函式（興櫃分析用）────────────
def _pf(v) -> float:
    try:
        s = str(v).replace(",", "").strip()
        return float(s) if s not in ("", "-", "--", "N/A", "nan") else 0.0
    except Exception:
        return 0.0

def _pi(v) -> int:
    try:
        s = str(v).replace(",", "").strip()
        return int(float(s)) if s not in ("", "-", "--") else 0
    except Exception:
        return 0

def _ma(closes: list, n: int) -> float:
    valid = [c for c in closes if c and c > 0]
    if not valid:
        return 0.0
    return sum(valid[-n:]) / len(valid[-n:])

def tpex_www_get(action: str):
    url = f"https://www.tpex.org.tw/www/zh-tw/{action}"
    try:
        r = requests.get(url, verify=False, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9",
            "Referer": "https://www.tpex.org.tw/zh-tw/esb/trading/info/pricing.html",
            "X-Requested-With": "XMLHttpRequest",
        })
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def _parse_tpex_www(raw) -> list:
    if not raw:
        return []
    t = None
    if isinstance(raw, dict):
        if "tables" in raw:
            tb = raw["tables"]
            t = tb[0] if isinstance(tb, list) and tb else tb
        elif "fields" in raw:
            t = raw
    if t and isinstance(t, dict):
        fields = t.get("fields", [])
        data   = t.get("data", [])
        rows   = []
        for row in data:
            if isinstance(row, list):
                rows.append(dict(zip(fields, row)))
            elif isinstance(row, dict):
                rows.append(row)
        return rows
    if isinstance(raw, list):
        return raw
    return []


# ── 興櫃股票分析 ──────────────────────────
# 資料來源：https://www.tpex.org.tw/www/zh-tw/emerging/latest
# 欄位：代號, 名稱, 前日均價, 報買價, 報買量, 報賣價, 報賣量,
#       日最高, 日最低, 日均價, 成交, 投資人成交買賣別, 成交量
@app.get("/emerging_analysis")
async def get_emerging_analysis(x_token: str = Header(default=None)):
    verify_token(x_token)

    today    = tw_now()
    start_90 = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    # 取 TPEX 興櫃即時行情
    rows = _parse_tpex_www(tpex_www_get("emerging/latest"))
    if not rows:
        return {"data": [], "total": 0,
                "error": "TPEX emerging/latest 無資料，請確認交易時段"}

    # 建立股票資料表
    stock_map = {}
    for r in rows:
        code = str(r.get("代號", "")).strip()
        name = str(r.get("名稱", "")).strip()
        if not code or not code.isdigit():
            continue
        price    = _pf(r.get("成交", 0))
        prev_avg = _pf(r.get("前日均價", 0))
        change   = round(price - prev_avg, 2) if price > 0 and prev_avg > 0 else 0.0
        vol      = _pi(r.get("成交量", 0))
        bid_vol  = _pi(r.get("報買量", 0))
        ask_vol  = _pi(r.get("報賣量", 0))
        direction = str(r.get("投資人成交買賣別", "")).strip()
        ratio    = bid_vol - ask_vol

        stock_map[code] = {
            "name": name, "price": price, "prev_avg": prev_avg,
            "change": change, "vol": vol,
            "bid_vol": bid_vol, "ask_vol": ask_vol,
            "ratio": ratio, "direction": direction,
        }

    # 篩選 + 20MA
    results = []
    for code, s in stock_map.items():
        try:
            price     = s["price"]
            change    = s["change"]
            vol       = s["vol"]
            bid_vol   = s["bid_vol"]
            ask_vol   = s["ask_vol"]
            ratio     = s["ratio"]
            direction = s["direction"]

            if price <= 0 or vol <= 0:    continue
            if vol   <= 100000:           continue   # 成交量 > 10萬
            if price <= 150:              continue   # 股價 > 150
            if ratio <= 1000:             continue   # 買賣比 > 1000
            if direction != "買進":       continue   # 買進方向

            # 20MA
            hist   = finmind_get("TaiwanStockPrice", code, start_90, end_date)
            closes = [float(x.get("close", 0)) for x in hist if x.get("close")]
            ma20   = _ma(closes, 20)
            if ma20 > 0 and price <= ma20:
                continue

            prev    = s["prev_avg"]
            chg_pct = round(change / prev * 100, 2) if prev > 0 else 0.0

            results.append({
                "code": code, "name": s["name"],
                "price": price, "change": change, "change_pct": chg_pct,
                "volume": vol, "bid_total": bid_vol, "ask_total": ask_vol,
                "ratio": ratio, "direction": direction,
                "ma20": round(ma20, 2),
                "above_ma20": (price > ma20) if ma20 > 0 else True,
                "has_quote": True,
            })
        except Exception:
            continue

    results.sort(key=lambda x: (-x["ratio"], -x["volume"]))
    return {
        "data": results, "total": len(results),
        "source_tpex": "https://www.tpex.org.tw/www/zh-tw/emerging/latest",
        "esb_total": len(stock_map), "has_quote": True,
    }
# 貼到 main.py 最後面，取代舊的 /foreign_rank

@app.get("/foreign_rank")
async def get_foreign_rank(x_token: str = Header(default=None)):
    verify_token(x_token)
    today = tw_now()

    for i in range(1, 8):
        d = (today - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?response=json&date={d}&selectType=ALL"
        data = twse_get(url)

        if not data or data.get("stat") != "OK":
            continue

        fields = data.get("fields", [])
        rows   = data.get("data", [])
        if not rows:
            continue

        # 實際欄位名稱：外陸資買進股數(不含外資自營商)
        def fi(candidates, default):
            for name in candidates:
                if name in fields:
                    return fields.index(name)
            return default

        idx_code  = fi(["證券代號"], 0)
        idx_name  = fi(["證券名稱"], 1)
        idx_fbuy  = fi(["外陸資買進股數(不含外資自營商)", "外陸資買進股數", "外資及陸資買進股數"], 2)
        idx_fsell = fi(["外陸資賣出股數(不含外資自營商)", "外陸資賣出股數", "外資及陸資賣出股數"], 3)
        idx_fnet  = fi(["外陸資買賣超股數(不含外資自營商)", "外陸資買賣超股數", "外資及陸資淨買賣超股數"], 4)

        def parse_num(s):
            try:
                return int(str(s).replace(",", "").replace(" ", "")) // 1000
            except Exception:
                return 0

        items = []
        for row in rows:
            try:
                code = str(row[idx_code]).strip()
                name = str(row[idx_name]).strip()
                if not code.isdigit():
                    continue
                buy  = parse_num(row[idx_fbuy])
                sell = parse_num(row[idx_fsell])
                net  = parse_num(row[idx_fnet])
                items.append({"code": code, "name": name,
                              "buy": buy, "sell": sell, "net": net})
            except Exception:
                continue

        if not items:
            continue

        buy_top  = sorted(items, key=lambda x: x["net"],  reverse=True)[:20]
        sell_top = sorted(items, key=lambda x: x["net"])[:20]
        date_str = f"{d[:4]}-{d[4:6]}-{d[6:]}"

        return {
            "date": date_str,
            "buy_top":  buy_top,
            "sell_top": sell_top,
            "total_stocks": len(items)
        }

    return {
        "date": "", "buy_top": [], "sell_top": [],
        "total_stocks": 0,
        "error": "無法取得資料（請確認為交易日）"
    }


# ── /chips/{symbol} 籌碼分析 API ─────────────
@app.get("/chips/{symbol}")
async def get_chips(symbol: str, x_token: str = Header(default=None)):
    """
    整合當日三大法人、融資融券、借券、當沖等籌碼資料
    """
    verify_token(x_token)
    today = tw_now()
    start_10 = (today - timedelta(days=20)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    # ── 1. 並行抓取 FinMind 資料，避免籌碼頁等待多個外部請求串行逾時 ─────
    institutional = {
        "foreign_net": 0,
        "foreign_buy": 0,
        "foreign_sell": 0,
        "invest_trust_net": 0,
        "invest_trust_buy": 0,
        "invest_trust_sell": 0,
        "dealer_net": 0,
        "dealer_buy": 0,
        "dealer_sell": 0,
    }
    history_rows = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        fut_inst = ex.submit(
            finmind_get,
            "TaiwanStockInstitutionalInvestorsBuySell",
            symbol,
            start_10,
            end_date,
        )
        fut_price = ex.submit(
            finmind_get,
            "TaiwanStockPrice",
            symbol,
            start_10,
            end_date,
        )
        fut_margin = ex.submit(
            finmind_get,
            "TaiwanStockMarginPurchaseShortSale",
            symbol,
            start_10,
            end_date,
        )
        fut_day_trade = ex.submit(
            finmind_get,
            "TaiwanStockDayTrading",
            symbol,
            start_10,
            end_date,
        )
        fut_shareholding = ex.submit(
            finmind_get,
            "TaiwanStockShareholding",
            symbol,
            start_10,
            end_date,
        )
        fut_short_bal = ex.submit(
            finmind_get,
            "TaiwanDailyShortSaleBalances",
            symbol,
            start_10,
            end_date,
        )
        inst_rows = fut_inst.result()
        price_rows = fut_price.result()
        margin_rows_raw = fut_margin.result()
        day_trade_rows = fut_day_trade.result()
        shareholding_rows = fut_shareholding.result()
        short_bal_rows = fut_short_bal.result()

    def to_int(value, default=0):
        try:
            return int(float(str(value).replace(",", "").strip()))
        except Exception:
            return default

    # ── 2. 近10日三大法人歷史（FinMind）──────────
    hist_map = {}
    for r in inst_rows:
        date_key = r["date"]
        if date_key not in hist_map:
            hist_map[date_key] = {
                "date": date_key,
                "foreign_net": 0,
                "foreign_buy": 0,
                "foreign_sell": 0,
                "invest_trust_net": 0,
                "invest_trust_buy": 0,
                "invest_trust_sell": 0,
                "dealer_net": 0,
                "dealer_buy": 0,
                "dealer_sell": 0,
            }
        buy  = max(int(r.get("buy",  0)), 0) // 1000
        sell = max(int(r.get("sell", 0)), 0) // 1000
        net  = buy - sell
        name = r.get("name", "")
        if name == "Foreign_Investor":
            hist_map[date_key]["foreign_net"] = net
            hist_map[date_key]["foreign_buy"] = buy
            hist_map[date_key]["foreign_sell"] = sell
        elif name == "Investment_Trust":
            hist_map[date_key]["invest_trust_net"] = net
            hist_map[date_key]["invest_trust_buy"] = buy
            hist_map[date_key]["invest_trust_sell"] = sell
        elif name == "Dealer_self":
            hist_map[date_key]["dealer_net"] = net
            hist_map[date_key]["dealer_buy"] = buy
            hist_map[date_key]["dealer_sell"] = sell

    # ── 加上收盤價 ──────────────────────────────
    price_map = {r["date"]: float(r.get("close", 0)) for r in price_rows}
    for date_key, row in hist_map.items():
        row["close"] = price_map.get(date_key, 0)

    history_rows = sorted(hist_map.values(), key=lambda x: x["date"])

    # ── 優先用 FinMind 最新一筆的 net ───────────
    # FinMind 已可提供 buy/sell/net；若沒有拆分欄位則保留預設 0。
    latest_inst_date = ""
    if history_rows:
        latest_hist      = history_rows[-1]
        latest_inst_date = latest_hist["date"]
        institutional = {
            "foreign_net":       latest_hist.get("foreign_net", institutional.get("foreign_net", 0)),
            "invest_trust_net":  latest_hist.get("invest_trust_net", institutional.get("invest_trust_net", 0)),
            "dealer_net":        latest_hist.get("dealer_net", institutional.get("dealer_net", 0)),
            "foreign_buy":       latest_hist.get("foreign_buy", institutional.get("foreign_buy", 0)),
            "foreign_sell":      latest_hist.get("foreign_sell", institutional.get("foreign_sell", 0)),
            "invest_trust_buy":  latest_hist.get("invest_trust_buy", institutional.get("invest_trust_buy", 0)),
            "invest_trust_sell": latest_hist.get("invest_trust_sell", institutional.get("invest_trust_sell", 0)),
            "dealer_buy":        latest_hist.get("dealer_buy", institutional.get("dealer_buy", 0)),
            "dealer_sell":       latest_hist.get("dealer_sell", institutional.get("dealer_sell", 0)),
        }

    # ── 3. 融資融券（FinMind）────────────────────
    margin_history = []
    for r in margin_rows_raw:
        mb  = int(r.get("MarginPurchaseTodayBalance", 0))
        mb_prev = int(r.get("MarginPurchaseYesterdayBalance", 0))
        sb  = int(r.get("ShortSaleTodayBalance", 0))
        sb_prev = int(r.get("ShortSaleYesterdayBalance", 0))
        margin_history.append({
            "date":           r["date"],
            "margin_balance": mb,
            "margin_change":  mb - mb_prev,
            "short_balance":  sb,
            "short_change":   sb - sb_prev,
            "short_margin_ratio": round(sb / mb * 100, 2) if mb > 0 else 0,
        })
    margin_history.sort(key=lambda x: x["date"])
    latest_margin = margin_history[-1] if margin_history else {}

    # ── 4. 當日股價與成交量（FinMind）─────────────
    latest_price_row = price_rows[-1] if price_rows else {}
    latest_price  = float(latest_price_row.get("close", 0))
    latest_volume = int(latest_price_row.get("Trading_Volume", 0)) // 1000

    # ── 5. 當沖率（FinMind TaiwanStockDayTrading）────────
    day_trade_vol = None
    day_trade_ratio = None
    if day_trade_rows:
        latest_day_trade = sorted(day_trade_rows, key=lambda x: x.get("date", ""))[-1]
        raw_day_trade_vol = to_int(latest_day_trade.get("Volume"), 0)
        day_trade_vol = raw_day_trade_vol // 1000
        day_trade_ratio = round(day_trade_vol / latest_volume * 100, 2) if latest_volume > 0 else None

    # ── 6. 周轉率（FinMind TaiwanStockShareholding）───────
    turnover_rate = None
    if shareholding_rows:
        latest_shareholding = sorted(shareholding_rows, key=lambda x: x.get("date", ""))[-1]
        issued_shares = to_int(
            latest_shareholding.get("NumberOfSharesIssued")
            or latest_shareholding.get("number_of_shares_issued"),
            0,
        )
        issued_lots = issued_shares // 1000
        turnover_rate = round(latest_volume / issued_lots * 100, 2) if issued_lots > 0 else None

    # ── 7. 借券賣出餘額（FinMind TaiwanDailyShortSaleBalances）──
    borrow_sell_change = None
    borrow_sell_balance = None
    if short_bal_rows:
        latest_short_bal = sorted(short_bal_rows, key=lambda x: x.get("date", ""))[-1]
        sbl_prev = to_int(latest_short_bal.get("SBLShortSalesPreviousDayBalance"), 0)
        sbl_current = to_int(latest_short_bal.get("SBLShortSalesCurrentDayBalance"), 0)
        borrow_sell_balance = sbl_current // 1000
        borrow_sell_change = int((sbl_current - sbl_prev) / 1000)

    # ── 組合今日籌碼 ─────────────────────────────
    data_out = {
        **institutional,
        "price":           latest_price,
        "volume":          latest_volume,
        "margin_balance":  latest_margin.get("margin_balance", 0),
        "margin_change":   latest_margin.get("margin_change", 0),
        "short_balance":   latest_margin.get("short_balance", 0),
        "short_change":    latest_margin.get("short_change", 0),
        "short_margin_ratio": latest_margin.get("short_margin_ratio", 0),
        "day_trade_volume": day_trade_vol,
        "day_trade_ratio":  day_trade_ratio,
        "turnover_rate": turnover_rate,
        "borrow_sell_change": borrow_sell_change,
        "borrow_sell_balance": borrow_sell_balance,
        # 主力 = 外資+投信（簡化）
        "main_net": (institutional.get("foreign_net", 0) + institutional.get("invest_trust_net", 0)),
        # 三大法人合計
        "institutional_total": (
            institutional.get("foreign_net", 0) +
            institutional.get("invest_trust_net", 0) +
            institutional.get("dealer_net", 0)
        ),
    }

    return {
        "data":           data_out,
        "history":        history_rows,
        "margin_history": margin_history[-10:],
        "source":         "finmind",
        "date":           latest_inst_date or end_date,
    }


@app.get("/chip_scan")
async def chip_scan(
    codes: str = "",
    min_foreign: int = 0,
    x_token: str = Header(default=None)
):
    verify_token(x_token)
    today = tw_now()

    code_list = [c.strip() for c in codes.split(",") if c.strip().isdigit()]
    if not code_list:
        return {"data": [], "error": "請提供股票代號", "scan_date": ""}

    scan_date = None
    for i in range(7):
        d = today - timedelta(days=i)
        if d.weekday() >= 5:
            continue
        scan_date = d.strftime("%Y-%m-%d")
        break

    if not scan_date:
        return {"data": [], "error": "無法判斷交易日", "scan_date": ""}

    results = []
    for code in code_list[:60]:
        try:
            rows = finmind_get(
                "TaiwanStockInstitutionalInvestorsBuySell",
                code, scan_date, scan_date
            )
            if not rows:
                continue

            foreign_buy = foreign_sell = trust_buy = trust_sell = 0
            stock_name = code
            for row in rows:
                name_type = row.get("name", "")
                buy = int(row.get("buy", 0))
                sell = int(row.get("sell", 0))
                if name_type == "Foreign_Investor":
                    foreign_buy = buy // 1000
                    foreign_sell = sell // 1000
                elif name_type == "Investment_Trust":
                    trust_buy = buy // 1000
                    trust_sell = sell // 1000

            foreign_net = foreign_buy - foreign_sell
            trust_net = trust_buy - trust_sell

            if foreign_net <= min_foreign or trust_net <= 0:
                continue

            try:
                ticker_rows = finmind_get("TaiwanStockInfo", code, "2020-01-01", scan_date)
                if ticker_rows:
                    stock_name = ticker_rows[-1].get("stock_name", code)
            except Exception:
                pass

            price_rows = finmind_get("TaiwanStockPrice", code, scan_date, scan_date)
            close = 0
            if price_rows:
                close = float(price_rows[-1].get("close", 0))

            results.append({
                "code": code,
                "name": stock_name,
                "close": close,
                "foreign_net": foreign_net,
                "trust_net": trust_net,
                "total_net": foreign_net + trust_net,
            })

        except Exception:
            continue

    results.sort(key=lambda x: -x["foreign_net"])
    return {
        "data": results,
        "scan_date": scan_date,
        "total": len(results),
        "note": f"共 {len(results)} 支雙買超，掃描 {len(code_list)} 支（{scan_date}）"
    }


# ════════════════════════════════════════════════════════════════
#  即時內外盤比 v4
#  最新成交價：intraday/trades 最後一筆，quote 僅作無逐筆資料時的 fallback
#  全日外盤/內盤：intraday/volumes 分價量表逐列加總
#  近100筆滾動：intraday/trades Tick Rule 推估
# ════════════════════════════════════════════════════════════════

_tick_cache: dict = {}
_TICK_CACHE_SEC = 12
_TW_TZ = timezone(timedelta(hours=8))

def _tick_float(v, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        s = str(v).replace(",", "").strip()
        if s in ("", "-", "--", "None", "null", "nan"):
            return default
        return float(s)
    except Exception:
        return default

def _tick_int(v, default: int = 0) -> int:
    return int(_tick_float(v, float(default)))

def _fmt_time(t) -> str:
    """Fugle time 欄位 → HH:MM:SS"""
    if t is None:
        return "—"

    def _from_unix(value) -> str | None:
        try:
            seconds = float(value)
        except Exception:
            return None

        # Fugle may return epoch timestamps in seconds, ms, us, or ns.
        magnitude = abs(seconds)
        if magnitude >= 1e17:
            seconds /= 1_000_000_000
        elif magnitude >= 1e14:
            seconds /= 1_000_000
        elif magnitude >= 1e11:
            seconds /= 1_000

        try:
            return datetime.fromtimestamp(seconds, _TW_TZ).strftime("%H:%M:%S")
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(t, (int, float)):
        return _from_unix(t) or str(t)[:8]

    s = str(t).strip()
    if not s:
        return "—"
    if "T" in s:
        try:
            return s.split("T")[1][:8]
        except Exception:
            pass
    if len(s) >= 8 and s[2] == ":" and s[5] == ":":
        return s[:8]

    parsed = _from_unix(s)
    return parsed or (s[:8] if len(s) >= 8 else s)

def _tick_err(symbol, msg):
    return {
        "symbol": symbol, "error": msg,
        "outer": 0, "inner": 0, "ratio": 50, "total": 0,
        "r_outer": 0, "r_inner": 0, "r_ratio": 50,
        "trade_count": 0, "trades": [], "latest_price": None,
    }

@app.get("/tick_ratio/{symbol}")
async def get_tick_ratio(symbol: str, x_token: str = Header(default=None)):
    """
    即時內外盤比 v4

    主要資料來源：
    - intraday/trades?limit=500&sort=desc → 最新500筆，再本地轉成舊到新做 Tick Rule
    - intraday/volumes → volumeAtAsk / volumeAtBid 分價量表加總（全日精確）
    - intraday/quote   → 只有完全沒有逐筆資料時，才用價格欄位 fallback
    - FinMind TaiwanStockPrice → quote 也無價時，最後用近10日最後收盤價 fallback

    latest_price 來源優先順序：
      1. detail[-1]['price']（最新500筆本地轉舊到新後的最後一筆成交價）
      2. quote 的 lastPrice / closePrice / price（無逐筆資料時 fallback）
      3. FinMind 最近收盤價（無逐筆且 quote 無價時 fallback）
    """
    verify_token(x_token)

    now = tw_now()
    cached = _tick_cache.get(symbol)
    if cached and (now - cached["time"]).total_seconds() < _TICK_CACHE_SEC:
        return cached["data"]

    quote_url  = f"{FUGLE_BASE}/intraday/quote/{symbol}"
    vol_url    = f"{FUGLE_BASE}/intraday/volumes/{symbol}"
    # 先抓最新500筆；不能用 sort=asc，否則會拿到開盤後最早500筆。
    trades_url = f"{FUGLE_BASE}/intraday/trades/{symbol}?limit=500&sort=desc"

    try:
        async with httpx.AsyncClient() as client:
            vol_res, trades_res = await asyncio.gather(
                client.get(vol_url,    headers={"X-API-KEY": FUGLE_API_KEY}, timeout=10),
                client.get(trades_url, headers={"X-API-KEY": FUGLE_API_KEY}, timeout=10),
            )
        vol_raw    = vol_res.json()
        trades_raw = trades_res.json()
    except Exception as e:
        return _tick_err(symbol, f"Fugle API 連線失敗：{e}")

    latest_price = None
    close_price = None
    close_date = ""

    # ── 全日：volumes 分價量表，逐列加總 ──────────────────────────
    vol_data = vol_raw.get("data", [])
    if isinstance(vol_data, list) and vol_data:
        outer_day = sum(_tick_int(row.get("volumeAtAsk")) for row in vol_data)
        inner_day = sum(_tick_int(row.get("volumeAtBid")) for row in vol_data)
    elif isinstance(vol_data, dict):
        # 防禦：萬一 API 回傳單一 dict
        outer_day = _tick_int(vol_data.get("volumeAtAsk"))
        inner_day = _tick_int(vol_data.get("volumeAtBid"))
    else:
        outer_day = inner_day = 0

    total_day = outer_day + inner_day
    ratio_day = round(outer_day / total_day * 100, 1) if total_day > 0 else 50.0

    # ── 近100筆：trades Tick Rule ─────────────────────────────────
    # Fugle 回傳最新→最舊，先反轉成舊→新，Tick Rule 才能正確比較前一筆。
    trades_data = trades_raw.get("data", [])
    trades_list = list(reversed(trades_data)) if isinstance(trades_data, list) else []
    detail = []
    last_price_tick = None
    last_side = "outer"

    for t in trades_list:
        try:
            price = _tick_float(t.get("price"))
            size  = _tick_int(t.get("size"))
            t_str = _fmt_time(t.get("time"))
        except Exception:
            continue
        if price <= 0:
            continue
        if last_price_tick is None:
            side = "outer"
        elif price > last_price_tick:
            side = "outer"
        elif price < last_price_tick:
            side = "inner"
        else:
            side = last_side
        last_side       = side
        last_price_tick = price
        detail.append({"time": t_str, "price": price, "size": size, "side": side})

    # 最新500筆反轉後 detail[-1] 是目前最新一筆成交，直接作為畫面現價。
    if detail:
        latest_price = detail[-1]["price"]
    else:
        try:
            async with httpx.AsyncClient() as client:
                quote_res = await client.get(
                    quote_url, headers={"X-API-KEY": FUGLE_API_KEY}, timeout=10
                )
            quote_raw = quote_res.json()
            quote_data = quote_raw.get("data", {}) or {}
            latest_price = (
                _tick_float(quote_data.get("lastPrice")) or
                _tick_float(quote_data.get("closePrice")) or
                _tick_float(quote_data.get("price")) or
                None
            )
        except Exception:
            latest_price = None

        if latest_price is None:
            try:
                fm_end = now.strftime("%Y-%m-%d")
                fm_start = (now - timedelta(days=10)).strftime("%Y-%m-%d")
                fm_url = (
                    f"https://api.finmindtrade.com/api/v4/data"
                    f"?dataset=TaiwanStockPrice&data_id={symbol}"
                    f"&start_date={fm_start}&end_date={fm_end}"
                    f"&token={FINMIND_TOKEN}"
                )
                async with httpx.AsyncClient() as client:
                    fm_res = await client.get(fm_url, timeout=10)
                fm_raw = fm_res.json()
                fm_rows = fm_raw.get("data", []) if fm_raw.get("msg") == "success" else []
                if fm_rows:
                    latest_row = fm_rows[-1]
                    close_price = _tick_float(latest_row.get("close")) or None
                    close_date = str(latest_row.get("date", ""))
                    latest_price = close_price
            except Exception:
                latest_price = None

    recent_100 = detail[-100:]
    r_outer = sum(t["size"] for t in recent_100 if t["side"] == "outer")
    r_inner = sum(t["size"] for t in recent_100 if t["side"] == "inner")
    r_total = r_outer + r_inner
    r_ratio = round(r_outer / r_total * 100, 1) if r_total > 0 else 50.0

    # fallback：volumes 沒資料時改用 tick rule 全日估算
    if total_day == 0 and detail:
        outer_day = sum(t["size"] for t in detail if t["side"] == "outer")
        inner_day = sum(t["size"] for t in detail if t["side"] == "inner")
        total_day = outer_day + inner_day
        ratio_day = round(outer_day / total_day * 100, 1) if total_day > 0 else 50.0

    if not detail and total_day == 0:
        return _tick_err(symbol, "無資料。可能原因：非交易時段、代號有誤，或 Fugle 未提供此股票資料。")

    result = {
        "symbol":       symbol,
        "outer":        outer_day,
        "inner":        inner_day,
        "total":        total_day,
        "ratio":        ratio_day,
        "r_outer":      r_outer,
        "r_inner":      r_inner,
        "r_ratio":      r_ratio,
        "trade_count":  len(detail),
        "latest_price": latest_price,
        "close_price":  close_price,
        "close_date":   close_date,
        "updated_at":   now.strftime("%H:%M:%S"),
        "trades":       detail[-100:],
    }

    _tick_cache[symbol] = {"data": result, "time": now}
    return result

# ════════════════════════════════════════════════════════════════
#  即時資金雷達 — 正式版後端
#  資料來源：TWSE MIS（盤中即時）+ TWSE OpenAPI（全市場名單）
#  貼到 main.py 最底部
# ════════════════════════════════════════════════════════════════

from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote
import time as _time

# ── MIS Headers ─────────────────────────────────────────────
MIS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":    "https://mis.twse.com.tw/stock/fibest.jsp",
    "Accept":     "application/json, text/plain, */*",
}

# ── 產業分類（用在資金流向彙整）───────────────────────────────
INDUSTRY_GROUPS = {
    "半導體業", "電腦及週邊設備業", "電子零組件業", "光電業",
    "通信網路業", "其他電子業", "電子通路業", "資訊服務業",
    "航運業", "金融業", "生技醫療業", "電機機械", "汽車工業",
    "鋼鐵工業", "建材營造業", "油電燃氣業", "觀光餐旅業",
    "貿易百貨業", "化學工業", "塑膠工業", "紡織纖維", "食品工業",
    "造紙工業", "橡膠工業", "玻璃陶瓷", "水泥工業",
}

# ── 全市場股票清單快取 ────────────────────────────────────────
_stock_list_cache: list = []      # [{code, name, industry, market}, ...]
_stock_list_fetched: str = ""     # 上次抓取日期

def _get_stock_list() -> list:
    """抓上市＋上櫃股票清單（含產業、市場別）"""
    global _stock_list_cache, _stock_list_fetched
    today = tw_now().strftime("%Y-%m-%d")
    if _stock_list_cache and _stock_list_fetched == today:
        return _stock_list_cache

    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo&start_date=2024-01-01"
        data = twse_get(url)
        if not data or data.get("msg") != "success":
            return _stock_list_cache
        rows = data.get("data", [])

        result = []
        for row in rows:
            code = str(row.get("stock_id", "")).strip()
            name = str(row.get("stock_name", "")).strip()
            stock_type = str(row.get("type", "")).strip().lower()
            industry = str(row.get("industry_category", "")).strip() or "其他"
            if stock_type not in {"twse", "tpex"}:
                continue
            if not code.isdigit() or len(code) != 4:
                continue
            result.append({
                "code":     code,
                "name":     name,
                "industry": industry,
                "market":   "tse" if stock_type == "twse" else "otc",
            })

        if result:
            _stock_list_cache = result
            _stock_list_fetched = today
        return _stock_list_cache if _stock_list_cache else result

    except Exception as e:
        return _stock_list_cache  # 回傳舊快取


def _mis_symbol(code: str, market: str = "tse") -> str:
    market = "otc" if str(market).lower() == "otc" else "tse"
    return f"{market}_{code}.tw"


# ── 即時流向快取 ───────────────────────────────────────────────
_flow_cache: dict = {}     # cache_key → result
_prev_flow:  dict = {}     # 上一次的產業流向（用來算「較上次」）

def _flow_cache_key() -> str:
    now = tw_now()
    slot = (now.hour * 60 + now.minute) // 3  # 3分鐘為單位
    return f"{now.date()}_{slot}"

def _prev_cache_key() -> str:
    now = tw_now()
    slot = (now.hour * 60 + now.minute) // 3 - 1
    return f"{now.date()}_{max(slot,0)}"

def _is_market_live(now: datetime | None = None) -> bool:
    """僅在台股盤中開放 Discord 自動推播。"""
    now = now or tw_now()
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return 540 <= minutes < 810  # 09:00 - 13:30


# ── TWSE MIS：分批抓上市＋上櫃股票即時價格 ─────────────────────
def _fetch_mis_batch(codes_tw: list) -> list:
    """
    codes_tw: ["tse_2330.tw", "tse_2317.tw", ...]
    回傳 MIS msgArray list
    """
    ex_ch = "|".join(codes_tw)
    url = (f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
           f"?ex_ch={ex_ch}&json=1&delay=0")
    try:
        r = requests.get(url, headers=MIS_HEADERS, timeout=12, verify=False)
        d = r.json()
        return d.get("msgArray", [])
    except:
        return []

def _parse_mis_row(row: dict, industry: str, name: str) -> dict | None:
    """解析 MIS 單筆資料"""
    try:
        # MIS 欄位說明：
        # c = 代號, n = 名稱
        # z = 成交價, y = 昨收, u = 漲停, w = 跌停
        # v = 累計成交量(張)
        # tv = 最近一筆成交量(張)
        code = str(
            row.get("c", row.get("@", "").split(".")[0].replace("tse_", "").replace("otc_", ""))
        ).strip()
        if not code or not code.isdigit() or len(code) != 4:
            return None

        price_str = str(row.get("z","0") or "0").replace(",","")
        prev_str  = str(row.get("y","0") or "0").replace(",","")
        vol_str   = str(row.get("v","0") or row.get("tv","0") or "0").replace(",","")

        price = float(price_str) if price_str and price_str != "-" else 0.0
        prev  = float(prev_str)  if prev_str  and prev_str  != "-" else 0.0
        vol   = int(float(vol_str)) if vol_str and vol_str != "-" else 0

        if price <= 0 or prev <= 0:
            return None

        change  = round(price - prev, 2)
        chg_pct = round(change / prev * 100, 2)

        # 成交金額（億元）= 張數 × 股價 × 1000股 ÷ 1億
        amount = round(vol * price * 1000 / 1e8, 2)

        # 資金流向：漲→流入，跌→流出，平→不計
        flow_in  = amount if chg_pct > 0 else 0.0
        flow_out = amount if chg_pct < 0 else 0.0
        net_flow = round(flow_in - flow_out, 2)

        stk_name = str(row.get("n", name or code)).strip()

        return {
            "code":     code,
            "name":     stk_name,
            "industry": industry,
            "price":    price,
            "prev":     prev,
            "change":   change,
            "chg_pct":  chg_pct,
            "vol":      vol,
            "amount":   amount,
            "flow_in":  flow_in,
            "flow_out": flow_out,
            "net_flow": net_flow,
        }
    except:
        return None


def _fetch_all_market() -> dict:
    """
    分批抓全市場即時資料
    回傳 {code: stock_dict}
    """
    stock_list = _get_stock_list()
    if not stock_list:
        return {}

    # 建立 code → {name, industry, market} 對照
    info_map = {s["code"]: s for s in stock_list}
    all_stocks = stock_list

    # 分批：每批 150 支（MIS URL長度限制）
    BATCH = 150
    batches = []
    for i in range(0, len(all_stocks), BATCH):
        batch_stocks = all_stocks[i:i+BATCH]
        codes_tw = [_mis_symbol(s["code"], s.get("market", "tse")) for s in batch_stocks]
        batches.append((batch_stocks, codes_tw))

    stock_data: dict = {}

    # 並行抓取（最多5個同時，避免被擋）
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {
            ex.submit(_fetch_mis_batch, codes_tw): batch_stocks
            for batch_stocks, codes_tw in batches
        }
        for future in as_completed(futures):
            batch_stocks = futures[future]
            try:
                rows = future.result()
                for row in rows:
                    # 從 @ 欄位取代號
                    at = str(row.get("@",""))
                    code = at.split(".")[0].replace("tse_","").replace("otc_","")
                    if not code:
                        code = str(row.get("c",""))
                    info = info_map.get(code, {})
                    parsed = _parse_mis_row(
                        row,
                        info.get("industry","其他"),
                        info.get("name","")
                    )
                    if parsed:
                        stock_data[code] = parsed
            except:
                pass

    return stock_data


def _build_industry_flow(stock_data: dict) -> dict:
    """彙整產業資金流向"""
    groups: dict = {}

    for s in stock_data.values():
        ind = s["industry"] or "其他"
        if ind not in groups:
            groups[ind] = {
                "name":        ind,
                "type":        "industry",
                "in_amount":   0.0,
                "out_amount":  0.0,
                "stocks":      [],
            }
        groups[ind]["in_amount"]  += s["flow_in"]
        groups[ind]["out_amount"] += s["flow_out"]
        groups[ind]["stocks"].append(s)

    # 計算淨額、集中度、取前5大個股
    result = {}
    for ind, g in groups.items():
        net   = round(g["in_amount"] - g["out_amount"], 2)
        total = g["in_amount"] + g["out_amount"]
        stocks_sorted = sorted(g["stocks"],
                               key=lambda x: abs(x["net_flow"]), reverse=True)
        conc = 0
        if total > 0 and stocks_sorted:
            conc = round(abs(stocks_sorted[0]["net_flow"]) / total * 100)

        result[ind] = {
            "name":          ind,
            "type":          "industry",
            "net_amount":    round(net, 2),
            "in_amount":     round(g["in_amount"], 2),
            "out_amount":    round(g["out_amount"], 2),
            "concentration": conc,
            "stock_count":   len(g["stocks"]),
            "stocks": [{
                "code":     s["code"],
                "name":     s["name"],
                "price":    s["price"],
                "chg_pct":  s["chg_pct"],
                "amount":   s["amount"],
                "net_flow": s["net_flow"],
            } for s in stocks_sorted[:5]],
        }
    return result


# ══════════════════════════════════════════════════════════════
#  Endpoint 1：全市場資金流向總覽  GET /flow/summary
#  ※ 3分鐘快取；第一次約15秒，之後很快
# ══════════════════════════════════════════════════════════════
@app.get("/flow/summary")
async def flow_summary(x_token: str = Header(default=None)):
    verify_token(x_token)

    ck = _flow_cache_key()
    if ck in _flow_cache:
        return {**_flow_cache[ck], "cached": True}

    t0 = _time.time()

    # 抓上市＋上櫃即時資料
    stock_data = _fetch_all_market()
    if not stock_data:
        return {"error": "無法取得市場資料", "industry": {}, "top_in": [], "top_out": []}

    # 彙整產業流向
    industry_flow = _build_industry_flow(stock_data)

    # 取上一次快取做「較上次」比較
    prev_ck = _prev_cache_key()
    prev_industry = _flow_cache.get(prev_ck, {}).get("industry", {})

    # 加上「較上次」差值
    for ind, g in industry_flow.items():
        prev_net = prev_industry.get(ind, {}).get("net_amount", None)
        if prev_net is not None:
            g["prev_net"]    = prev_net
            g["prev_change"] = round(g["net_amount"] - prev_net, 2)
        else:
            g["prev_net"]    = None
            g["prev_change"] = None

    # 個股排行
    all_s   = list(stock_data.values())
    top_in  = sorted([s for s in all_s if s["chg_pct"] > 0],
                     key=lambda x: x["flow_in"], reverse=True)[:20]
    top_out = sorted([s for s in all_s if s["chg_pct"] < 0],
                     key=lambda x: x["flow_out"], reverse=True)[:20]

    elapsed = round(_time.time() - t0, 1)
    result = {
        "industry":    industry_flow,
        "top_in":      top_in,
        "top_out":     top_out,
        "_stock_data": stock_data,
        "scanned":     len(stock_data),
        "elapsed_sec": elapsed,
        "updated_at":  tw_now().strftime("%H:%M"),
        "data_date":   tw_now().strftime("%Y-%m-%d"),
        "cached":      False,
    }

    # 存快取（只保留最近6筆 = 30分鐘）
    _flow_cache[ck] = result
    if len(_flow_cache) > 6:
        del _flow_cache[next(iter(_flow_cache))]

    return result


# ══════════════════════════════════════════════════════════════
#  Endpoint 2：個股流向詳細  GET /flow/stock/{code}
#  回傳今日即時 + 近20日歷史（用FinMind單股查詢，免費版可用）
# ══════════════════════════════════════════════════════════════
@app.get("/flow/stock/{code}")
async def flow_stock(code: str, x_token: str = Header(default=None)):
    verify_token(x_token)

    stock_list = _get_stock_list()
    info_map = {s["code"]: s for s in stock_list}
    info = info_map.get(code, {})

    # 即時資料：MIS 單股
    mis_rows = _fetch_mis_batch([_mis_symbol(code, info.get("market", "tse"))])
    latest = {}
    if mis_rows:
        parsed = _parse_mis_row(mis_rows[0], info.get("industry",""), info.get("name",""))
        if parsed:
            latest = parsed

    # 歷史資料：FinMind 單股（免費版可用）
    today = tw_now()
    start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    end   = today.strftime("%Y-%m-%d")

    price_rows = finmind_get("TaiwanStockPrice", code, start, end)
    inst_rows  = finmind_get("TaiwanStockInstitutionalInvestorsBuySell", code, start, end)

    # 法人按日期整理
    inst_map: dict = {}
    for row in inst_rows:
        d = row.get("date","")
        inst_map.setdefault(d, {"foreign":0,"trust":0,"dealer":0})
        n = row.get("name","")
        b = max(int(row.get("buy",0)),0) // 1000
        s = max(int(row.get("sell",0)),0) // 1000
        if n == "Foreign_Investor":   inst_map[d]["foreign"] = b - s
        elif n == "Investment_Trust": inst_map[d]["trust"]   = b - s
        elif n == "Dealer_self":      inst_map[d]["dealer"]  = b - s

    latest_inst = {"foreign": 0, "trust": 0, "dealer": 0}
    if inst_map:
        latest_inst = inst_map[sorted(inst_map.keys())[-1]]

    latest.update({
        "foreign_net": latest_inst.get("foreign", 0),
        "trust_net":   latest_inst.get("trust", 0),
        "dealer_net":  latest_inst.get("dealer", 0),
        "inst_total": (
            latest_inst.get("foreign", 0)
            + latest_inst.get("trust", 0)
            + latest_inst.get("dealer", 0)
        ),
    })

    # 找所屬產業/主題
    info = next((s for s in stock_list if s["code"] == code), {})
    name     = latest.get("name") or info.get("name", code)
    industry = info.get("industry","")
    belongs_to = [{"name": industry, "type": "industry"}] if industry else []

    # 時間軸（近20日，最新在前）
    timeline = []
    for row in reversed(price_rows[-20:]):
        d       = row.get("date","")
        price   = float(row.get("close",0) or 0)
        change  = float(row.get("change",0) or 0)
        prev_p  = price - change
        chg_pct = round(change/prev_p*100, 2) if prev_p > 0 else 0.0
        vol     = int(row.get("Trading_Volume",0) or 0)
        money   = float(row.get("Trading_money",0) or 0)
        amount  = round(money/1e8, 2) if money > 0 else round(vol*price*1000/1e8, 2)
        inst    = inst_map.get(d, {})
        fn = inst.get("foreign",0)
        tn = inst.get("trust",0)
        dn = inst.get("dealer",0)
        timeline.append({
            "date":        d,
            "price":       price,
            "change":      change,
            "chg_pct":     chg_pct,
            "amount":      amount,
            "net_flow":    round(amount if chg_pct>=0 else -amount, 2),
            "flow_dir":    "in" if chg_pct >= 0 else "out",
            "foreign_net": fn,
            "trust_net":   tn,
            "dealer_net":  dn,
            "inst_total":  fn + tn + dn,
        })

    return {
        "code":       code,
        "name":       name,
        "industry":   industry,
        "belongs_to": belongs_to,
        "latest":     latest,
        "timeline":   timeline,
        "updated_at": tw_now().strftime("%H:%M"),
    }


# ══════════════════════════════════════════════════════════════
#  Endpoint 3：產業詳細  GET /flow/industry/{name}
# ══════════════════════════════════════════════════════════════
@app.get("/flow/industry/{name}")
async def flow_industry(name: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    name = unquote(name)

    # 從快取取最新資料
    ck = _flow_cache_key()
    cached = _flow_cache.get(ck) or _flow_cache.get(_prev_cache_key())

    if cached and name in cached.get("industry", {}):
        ind_data = cached["industry"][name]
        # 從快取裡拿完整股票資料，避免只剩 summary 的前 5 檔縮略資料
        stock_data = cached.get("_stock_data", {})
        full_stocks = [
            s for s in stock_data.values()
            if s.get("industry") == name
        ]
        total_a = sum(s["amount"] for s in full_stocks) or 1
        stocks_out = []
        for s in sorted(full_stocks, key=lambda x: abs(x["net_flow"]), reverse=True):
            pct = round(abs(s["net_flow"]) / total_a * 100)
            stocks_out.append({**s, "pct": pct})
        return {
            "name":       name,
            "net_amount": ind_data["net_amount"],
            "in_amount":  ind_data["in_amount"],
            "out_amount": ind_data["out_amount"],
            "prev_change": ind_data.get("prev_change"),
            "stocks":     stocks_out,
            "updated_at": cached.get("updated_at",""),
        }

    # 快取沒有 → 即時抓這個產業的股票
    stock_list = _get_stock_list()
    stocks_in_industry = [s for s in stock_list if s["industry"] == name]
    if not stocks_in_industry:
        return {"error": f"找不到產業：{name}", "stocks": []}

    codes_tw = [_mis_symbol(s["code"], s.get("market", "tse")) for s in stocks_in_industry]
    rows = _fetch_mis_batch(codes_tw)

    info_map = {s["code"]: s for s in stock_list}
    stocks = []
    for row in rows:
        at   = str(row.get("@",""))
        code = at.split(".")[0].replace("tse_","").replace("otc_","")
        info = info_map.get(code, {})
        p = _parse_mis_row(row, name, info.get("name",""))
        if p:
            stocks.append(p)

    in_a  = sum(s["flow_in"]  for s in stocks)
    out_a = sum(s["flow_out"] for s in stocks)
    total_a = in_a + out_a or 1

    stocks_sorted = sorted(stocks, key=lambda x: abs(x["net_flow"]), reverse=True)
    stocks_out = [{**s, "pct": round(abs(s["net_flow"])/total_a*100)} for s in stocks_sorted]

    return {
        "name":       name,
        "net_amount": round(in_a - out_a, 2),
        "in_amount":  round(in_a, 2),
        "out_amount": round(out_a, 2),
        "prev_change": None,
        "stocks":     stocks_out,
        "updated_at": tw_now().strftime("%H:%M"),
    }


# ══════════════════════════════════════════════════════════════
#  Endpoint 4：狀態確認  GET /flow/status
# ══════════════════════════════════════════════════════════════
@app.get("/flow/status")
async def flow_status(x_token: str = Header(default=None)):
    verify_token(x_token)
    ck  = _flow_cache_key()
    has = ck in _flow_cache
    return {
        "ok":          True,
        "has_cache":   has,
        "scanned":     _flow_cache[ck].get("scanned", 0) if has else 0,
        "updated_at":  _flow_cache[ck].get("updated_at","") if has else "",
        "elapsed_sec": _flow_cache[ck].get("elapsed_sec","") if has else "",
        "cache_key":   ck,
        "stock_list_count": len(_stock_list_cache),
    }


# ════════════════════════════════════════════════════════════════
#  Discord 警示系統
# ════════════════════════════════════════════════════════════════

# 已推播記錄（避免同一個訊號重複推播）
# key = "產業名稱_cache_key" or "股票代號_cache_key"
_alerted: set = set()
_monitor_discord_enabled = True

def _fmt_yi(v: float) -> str:
    """格式化億元"""
    a = abs(v)
    s = "+" if v >= 0 else "-"
    if a >= 10000: return f"{s}{a/10000:.1f}兆"
    if a >= 1:     return f"{s}{a:.2f}億"
    return f"{s}{a*100:.0f}百萬"

def send_discord(msg: str) -> bool:
    """發送 Discord Webhook 訊息"""
    if not DISCORD_WEBHOOK:
        return False
    try:
        r = requests.post(
            DISCORD_WEBHOOK,
            json={"content": msg},
            timeout=8
        )
        return r.status_code in (200, 204)
    except Exception:
        return False

def _prune_alerted(current_ck: str):
    """只保留目前與上一個 cache slot 的推播記錄，避免集合無限成長"""
    prev_ck = _prev_cache_key()
    keep = {
        key for key in _alerted
        if key.endswith(f"_{current_ck}") or key.endswith(f"_{prev_ck}")
    }
    _alerted.clear()
    _alerted.update(keep)

async def _check_and_alert(flow_result: dict, ind_thr: float, stock_thr: float):
    """
    掃描流向結果，超過門檻就推播 Discord
    ind_thr   : 產業流入警示門檻（億元）
    stock_thr : 個股流入警示門檻（億元）
    """
    ck = _flow_cache_key()
    alert_jobs = []
    push_time = tw_now()
    push_time_str = push_time.strftime("%H:%M:%S")
    data_time_str = flow_result.get("updated_at", "") or "—"

    # ── 1. 產業警示 ─────────────────────────────────────────
    for ind, g in flow_result.get("industry", {}).items():
        net = g.get("net_amount", 0)
        if net < ind_thr:
            continue
        alert_key = f"ind_{ind}_{ck}"
        if alert_key in _alerted:
            continue

        # 前5大個股
        top_stocks = g.get("stocks", [])[:5]
        stock_lines = "\n".join([
            f"  {i+1}. **{s['code']} {s.get('name','')}** "
            f"{'+' if s['chg_pct']>=0 else ''}{s['chg_pct']:.2f}%  "
            f"〔流入 {_fmt_yi(s['net_flow'])}〕"
            for i, s in enumerate(top_stocks)
        ])

        conc = g.get("concentration", 0)
        conc_str = "⚠️ 高度集中" if conc >= 70 else "中度集中" if conc >= 40 else "低度集中"

        prev_change = g.get("prev_change")
        prev_str = f"較上次 ↑{_fmt_yi(prev_change)}" if prev_change and prev_change > 0 else ""

        msg = (
            f"💰 **{ind}** 🔴資金流入\n"
            f"資料時間：{data_time_str}\n"
            f"推播時間：{push_time_str}\n\n"
            f"淨額：**{_fmt_yi(net)}**　{prev_str}\n"
            f"流入：{_fmt_yi(g.get('in_amount',0))} ｜ 流出：{_fmt_yi(g.get('out_amount',0))}\n"
            f"資金集中度：{conc}%（{conc_str}）\n\n"
            f"前 {len(top_stocks)} 大影響個股：\n{stock_lines}"
        )
        alert_jobs.append((alert_key, msg))

    # ── 2. 個股警示（流入 TOP 榜）────────────────────────────
    for s in flow_result.get("top_in", []):
        if s.get("flow_in", 0) < stock_thr:
            break  # 已排序，後面都不會超過
        alert_key = f"stk_{s['code']}_{ck}"
        if alert_key in _alerted:
            continue

        msg = (
            f"🚨 **{s['code']} {s.get('name','')}**　資金大量流入\n"
            f"資料時間：{data_time_str}\n"
            f"推播時間：{push_time_str}\n\n"
            f"現價：**{s['price']:.1f}**　"
            f"漲跌：**{'+' if s['chg_pct']>=0 else ''}{s['chg_pct']:.2f}%**\n"
            f"成交額：{s.get('amount',0):.2f}億　"
            f"流入：**{_fmt_yi(s['flow_in'])}**\n"
            f"產業：{s.get('industry','—')}"
        )
        alert_jobs.append((alert_key, msg))

    # ── 3. 批次發送（每則間隔0.5秒避免被擋）────────────────
    sent_count = 0
    for alert_key, msg in alert_jobs[:5]:  # 每次最多推 5 則，避免洗版
        ok = await asyncio.to_thread(send_discord, msg)
        if ok:
            _alerted.add(alert_key)
            sent_count += 1
        await asyncio.sleep(0.5)

    _prune_alerted(ck)
    return sent_count


# ══════════════════════════════════════════════════════════════
#  Endpoint 5：手動觸發監控掃描  POST /flow/monitor
#  前端每5分鐘自動呼叫，或手動測試
# ══════════════════════════════════════════════════════════════
@app.post("/flow/monitor")
async def flow_monitor(
    x_token: str = Header(default=None),
    ind_thr:   float = 20.0,   # 產業流入警示門檻（億），預設20億
    stock_thr: float = 5.0,    # 個股流入警示門檻（億），預設5億
):
    """
    掃描資金流向並推播 Discord 警示
    - ind_thr:   產業流入門檻（億元），超過就推播
    - stock_thr: 個股流入門檻（億元），超過就推播
    使用方式：POST /flow/monitor?ind_thr=30&stock_thr=10
    """
    verify_token(x_token)

    now = tw_now()

    # 取最新快取（沒有就重新抓）
    ck = _flow_cache_key()
    if ck in _flow_cache:
        flow_result = _flow_cache[ck]
    else:
        # 沒快取就重新抓全市場
        t0 = _time.time()
        stock_data = _fetch_all_market()
        if not stock_data:
            return {"ok": False, "error": "無法取得市場資料", "alerted": 0}
        industry_flow = _build_industry_flow(stock_data)
        prev_ck = _prev_cache_key()
        prev_industry = _flow_cache.get(prev_ck, {}).get("industry", {})
        for ind, g in industry_flow.items():
            prev_net = prev_industry.get(ind, {}).get("net_amount", None)
            g["prev_net"]    = prev_net
            g["prev_change"] = round(g["net_amount"] - prev_net, 2) if prev_net is not None else None

        all_s   = list(stock_data.values())
        top_in  = sorted([s for s in all_s if s["chg_pct"] > 0],
                         key=lambda x: x["flow_in"], reverse=True)[:20]
        top_out = sorted([s for s in all_s if s["chg_pct"] < 0],
                         key=lambda x: x["flow_out"], reverse=True)[:20]

        elapsed = round(_time.time() - t0, 1)
        flow_result = {
            "industry":    industry_flow,
            "top_in":      top_in,
            "top_out":     top_out,
            "_stock_data": stock_data,
            "scanned":     len(stock_data),
            "elapsed_sec": elapsed,
            "updated_at":  tw_now().strftime("%H:%M"),
            "data_date":   tw_now().strftime("%Y-%m-%d"),
            "cached":      False,
        }
        _flow_cache[ck] = flow_result

    if not _is_market_live(now):
        return {
            "ok":          True,
            "alerted":     0,
            "ind_thr":     ind_thr,
            "stock_thr":   stock_thr,
            "scanned":     flow_result.get("scanned", 0),
            "updated_at":  flow_result.get("updated_at", ""),
            "discord_set": bool(DISCORD_WEBHOOK),
            "checked_at":  now.strftime("%H:%M:%S"),
            "market_live": False,
            "message":     "目前非盤中時段，已跳過 Discord 推播",
        }

    # 執行警示檢查
    alerted_count = await _check_and_alert(flow_result, ind_thr, stock_thr)

    return {
        "ok":          True,
        "alerted":     alerted_count,
        "ind_thr":     ind_thr,
        "stock_thr":   stock_thr,
        "scanned":     flow_result.get("scanned", 0),
        "updated_at":  flow_result.get("updated_at", ""),
        "discord_set": bool(DISCORD_WEBHOOK),
        "checked_at":  now.strftime("%H:%M:%S"),
        "market_live": True,
    }


# ══════════════════════════════════════════════════════════════
#  Endpoint 6：Discord 測試  POST /flow/test_discord
# ══════════════════════════════════════════════════════════════
@app.post("/flow/test_discord")
async def test_discord(x_token: str = Header(default=None)):
    """測試 Discord Webhook 是否正常"""
    verify_token(x_token)
    if not DISCORD_WEBHOOK:
        return {"ok": False, "error": "DISCORD_WEBHOOK 環境變數未設定"}
    now = tw_now()
    ok = await asyncio.to_thread(send_discord,
        f"✅ **股票雷達連線成功！**\n"
        f"資料時間：測試訊息\n"
        f"推播時間：{now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Railway 後端正常運作，Discord 警示已啟用 🎉\n"
        f"產業流入門檻：20億　個股流入門檻：5億"
    )
    return {"ok": ok, "webhook_set": True}


def _build_pullback_discord_msg(
    code: str,
    name: str,
    price: float,
    prev_low: float,
    day_low: float,
    break_level: float,
    signal: str,
    note: str,
    now: datetime,
    is_test: bool = False,
) -> str:
    icon = "⚡" if signal == "假跌破回站" else "🟢" if signal == "守住昨低" else "❌"
    title_kind = "買點" if signal == "假跌破回站" else "觀察" if signal == "守住昨低" else "風控"
    test_prefix = "【測試】" if is_test else ""

    if signal == "假跌破回站":
        action = "可行動：這是本策略最強買點，但不是無條件追價；需確認站回 VWAP / 5MA，或出現紅K承接後再試單"
        stop = f"停損：再次跌破昨低 {prev_low:g}，或進場後跌破今低 {day_low:g}，立即出場"
    elif signal == "守住昨低":
        action = "可行動：先觀察，不急著追；需確認站穩 VWAP / 5MA，或出現紅K承接後再分批試單"
        stop = f"停損：跌破昨低 {prev_low:g} 或跌破昨低 1%（{break_level:g}）立即出場"
    elif signal == "跳空破低":
        action = "可行動：不進場；若已持有，不等盤中確認，優先風控出場"
        stop = "重新觀察條件：收盤重新站回昨低，且隔日不再破低"
    else:
        action = "可行動：不進場；若已持有，今日出局，停止監測此股"
        stop = "重新觀察條件：收盤重新站回昨低，且隔日不再破低"

    return (
        f"{icon} **{test_prefix}隔日沖{title_kind}｜{signal}**\n"
        f"{code} {name}\n"
        f"現價：{price:g} ｜ 昨低：{prev_low:g} ｜ 今低：{day_low:g}\n"
        f"判斷：{note}\n"
        f"{action}\n"
        f"{stop}\n"
        f"交易限制：此訊號需能盤中停損；零股無法當沖，僅建議紙上交易測試\n"
        f"資料時間：{now.strftime('%H:%M')}\n"
        f"推播時間：{now.strftime('%H:%M:%S')}"
    )


@app.post("/pullback_monitor")
async def pullback_monitor(body: dict, x_token: str = Header(default=None)):
    """盤中監測隔日沖候選：守昨低、假跌破回站、確認破低。"""
    verify_token(x_token)
    candidates = body.get("candidates", []) or []
    now = tw_now()
    minutes = now.hour * 60 + now.minute
    disposal_codes = _fetch_disposal_stocks()

    clean = []
    blocked_results = []
    for c in candidates[:50]:
        code = str(c.get("code", "")).strip()
        if not code.isdigit() or len(code) != 4:
            continue
        try:
            prev_low = float(c.get("prev_low", 0) or 0)
        except Exception:
            prev_low = 0
        if prev_low <= 0:
            continue
        market = str(c.get("market", "tse")).lower()
        if code in disposal_codes:
            blocked_results.append({
                "code": code,
                "name": str(c.get("name", code)).strip() or code,
                "price": 0,
                "day_low": 0,
                "prev_low": prev_low,
                "break_level": round(prev_low * 0.99, 2),
                "signal": "處置警示",
                "signal_type": "red",
                "note": "已列入處置/警示股，停止監測；此策略不適用",
            })
            continue
        clean.append({
            "code": code,
            "name": str(c.get("name", code)).strip() or code,
            "market": "otc" if market == "otc" else "tse",
            "prev_low": prev_low,
        })

    if not clean:
        return {
            "results": blocked_results,
            "market_live": _is_market_live(now),
            "discord_enabled": _monitor_discord_enabled,
            "pushed": [],
            "updated_at": now.strftime("%H:%M:%S"),
        }

    symbols = [_mis_symbol(c["code"], c["market"]) for c in clean]
    rows = _fetch_mis_batch(symbols)
    row_map = {}
    for row in rows:
        code = str(row.get("c", row.get("@", "").split(".")[0].replace("tse_", "").replace("otc_", ""))).strip()
        if code:
            row_map[code] = row

    results = blocked_results[:]
    pushed = []
    market_live = _is_market_live(now)

    for c in clean:
        row = row_map.get(c["code"], {})
        try:
            price = float(str(row.get("z", "0") or "0").replace(",", ""))
        except Exception:
            price = 0
        try:
            day_low = float(str(row.get("l", "0") or "0").replace(",", ""))
        except Exception:
            day_low = 0
        if day_low <= 0:
            day_low = price
        if price <= 0:
            results.append({
                "code": c["code"],
                "name": c["name"],
                "price": 0,
                "day_low": 0,
                "prev_low": c["prev_low"],
                "break_level": round(c["prev_low"] * 0.99, 2),
                "signal": "資料等待",
                "signal_type": "neutral",
                "note": "MIS 暫無即時價，保留候選並於下一輪再監測",
            })
            continue

        prev_low = c["prev_low"]
        name = str(row.get("n", c["name"])).strip() or c["name"]
        break_level = round(prev_low * 0.99, 2)

        if not market_live:
            signal = "非盤中"
            signal_type = "neutral"
            note = "非盤中時段，只顯示參考價；09:00-13:30 才判斷入場訊號"
        elif minutes <= 545 and price < break_level:
            signal = "跳空破低"
            signal_type = "red"
            note = "開盤跳空跌破昨低，直接風控出場"
        elif price < break_level:
            signal = "確認破低"
            signal_type = "red"
            note = "不進場；若已持有，今日出局"
        elif day_low < prev_low and price >= prev_low:
            signal = "假跌破回站"
            signal_type = "yellow"
            note = "最強買點，可考慮進場"
        elif price >= prev_low and minutes >= 570:
            signal = "守住昨低"
            signal_type = "green"
            note = "可觀察分批試單"
        else:
            signal = "盤中觀察"
            signal_type = "neutral"
            note = "等待 09:30 後確認"

        result = {
            "code": c["code"],
            "name": name,
            "price": price,
            "day_low": day_low,
            "prev_low": prev_low,
            "break_level": break_level,
            "signal": signal,
            "signal_type": signal_type,
            "note": note,
        }
        results.append(result)

        if not market_live or signal_type == "neutral" or not _monitor_discord_enabled:
            continue

        slot = _flow_cache_key()
        alert_key = f"pullback_{signal}_{c['code']}_{slot if signal == '守住昨低' else now.date()}"
        if alert_key in _alerted:
            continue

        msg = _build_pullback_discord_msg(c["code"], name, price, prev_low, day_low, break_level, signal, note, now)
        if send_discord(msg):
            _alerted.add(alert_key)
            pushed.append(c["code"])

    return {
        "results": results,
        "market_live": market_live,
        "discord_enabled": _monitor_discord_enabled,
        "pushed": pushed,
        "updated_at": now.strftime("%H:%M:%S"),
    }


@app.post("/pullback_monitor/discord_on")
async def pullback_monitor_discord_on(x_token: str = Header(default=None)):
    verify_token(x_token)
    global _monitor_discord_enabled
    _monitor_discord_enabled = True
    return {"discord_enabled": True}


@app.post("/pullback_monitor/discord_off")
async def pullback_monitor_discord_off(x_token: str = Header(default=None)):
    verify_token(x_token)
    global _monitor_discord_enabled
    _monitor_discord_enabled = False
    return {"discord_enabled": False}


@app.post("/pullback_monitor/test_discord")
async def test_pullback_monitor_discord(body: dict = None, x_token: str = Header(default=None)):
    """測試隔日沖盤中監測 Discord 文案，不受盤中時間限制。"""
    verify_token(x_token)
    if not DISCORD_WEBHOOK:
        return {"ok": False, "error": "DISCORD_WEBHOOK 環境變數未設定"}

    body = body or {}
    requested = str(body.get("signal", "all")).strip()
    samples = {
        "假跌破回站": {
            "code": "2495", "name": "普安", "price": 40.85,
            "prev_low": 39.05, "day_low": 38.10, "note": "最強買點，可考慮進場",
        },
        "守住昨低": {
            "code": "3714", "name": "富采", "price": 64.90,
            "prev_low": 65.40, "day_low": 62.50, "note": "可觀察分批試單",
        },
        "確認破低": {
            "code": "3450", "name": "聯鈞", "price": 301.50,
            "prev_low": 309.65, "day_low": 300.10, "note": "不進場；若已持有，今日出局",
        },
        "跳空破低": {
            "code": "1802", "name": "台玻", "price": 61.20,
            "prev_low": 63.10, "day_low": 61.00, "note": "開盤跳空跌破昨低，直接風控出場",
        },
    }

    selected = samples if requested == "all" else {requested: samples[requested]} if requested in samples else {}
    if not selected:
        return {"ok": False, "error": "signal 必須是 all、假跌破回站、守住昨低、確認破低、跳空破低"}

    now = tw_now()
    pushed = []
    for signal, sample in selected.items():
        prev_low = float(sample["prev_low"])
        break_level = round(prev_low * 0.99, 2)
        msg = _build_pullback_discord_msg(
            sample["code"], sample["name"], float(sample["price"]), prev_low,
            float(sample["day_low"]), break_level, signal, sample["note"], now, is_test=True
        )
        ok = await asyncio.to_thread(send_discord, msg)
        if ok:
            pushed.append(signal)
        await asyncio.sleep(0.5)

    return {"ok": len(pushed) == len(selected), "pushed": pushed, "webhook_set": True}
