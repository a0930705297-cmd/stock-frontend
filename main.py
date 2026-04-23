import httpx
import requests
import warnings
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import yfinance as yf

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
    today = datetime.today()
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
    today = datetime.today()
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
    today = datetime.today()
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
    today = datetime.today()
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
        elapsed = (datetime.now() - cached["time"]).total_seconds() / 60
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
            "time": datetime.now()
        }
        print(f"新分析已快取：{cache_key}")

        return {"analysis": text, "cached": False}
    except Exception as e:
        return {"analysis": f"分析生成失敗：{str(e)}", "cached": False}

@app.get("/revenue/{symbol}")
async def get_revenue(symbol: str, x_token: str = Header(default=None)):
    verify_token(x_token)
    today = datetime.today()
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
    today = datetime.today()
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
    today = datetime.today()
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
    today = datetime.today()
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

    today    = datetime.today()
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
    today = datetime.today()

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
    today = datetime.today()

    # ── 1. 三大法人（TWSE T86，最近交易日）───────
    institutional = {}
    history_rows = []
    for i in range(1, 8):
        d = (today - timedelta(days=i)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/fund/T86?response=json&date={d}&selectType=ALL"
        data = twse_get(url)
        if not data or data.get("stat") != "OK":
            continue
        fields = data.get("fields", [])
        rows   = data.get("data", [])

        def fi(candidates, default):
            for name in candidates:
                if name in fields:
                    return fields.index(name)
            return default

        idx_code   = fi(["證券代號"], 0)
        idx_name   = fi(["證券名稱"], 1)
        idx_fbuy   = fi(["外陸資買進股數(不含外資自營商)", "外陸資買進股數"], 2)
        idx_fsell  = fi(["外陸資賣出股數(不含外資自營商)", "外陸資賣出股數"], 3)
        idx_fnet   = fi(["外陸資買賣超股數(不含外資自營商)", "外陸資買賣超股數"], 4)
        idx_itbuy  = fi(["投信買進股數"], 8)
        idx_itsell = fi(["投信賣出股數"], 9)
        idx_itnet  = fi(["投信買賣超股數"], 10)
        idx_dbuy   = fi(["自營商買進股數(自行買賣)", "自營商買進股數"], 12)
        idx_dsell  = fi(["自營商賣出股數(自行買賣)", "自營商賣出股數"], 13)
        idx_dnet   = fi(["自營商買賣超股數(自行買賣)", "自營商買賣超股數"], 11)

        def pn(s):
            try: return int(str(s).replace(",","").strip()) // 1000
            except: return 0

        for row in rows:
            try:
                if str(row[idx_code]).strip() != symbol:
                    continue
                institutional = {
                    "foreign_net":      pn(row[idx_fnet]),
                    "foreign_buy":      pn(row[idx_fbuy]),
                    "foreign_sell":     pn(row[idx_fsell]),
                    "invest_trust_net": pn(row[idx_itnet]),
                    "invest_trust_buy": pn(row[idx_itbuy]),
                    "invest_trust_sell":pn(row[idx_itsell]),
                    "dealer_net":       pn(row[idx_dnet]),
                    "dealer_buy":       pn(row[idx_dbuy]),
                    "dealer_sell":      pn(row[idx_dsell]),
                }
                break
            except Exception:
                continue
        if institutional:
            break

    # ── 2. 近10日三大法人歷史（FinMind）──────────
    start_10 = (today - timedelta(days=20)).strftime("%Y-%m-%d")
    end_date  = today.strftime("%Y-%m-%d")
    inst_rows = finmind_get("TaiwanStockInstitutionalInvestorsBuySell", symbol, start_10, end_date)
    hist_map = {}
    for r in inst_rows:
        date_key = r["date"]
        if date_key not in hist_map:
            hist_map[date_key] = {"date": date_key, "foreign_net": 0, "invest_trust_net": 0, "dealer_net": 0}
        buy  = max(int(r.get("buy",  0)), 0) // 1000
        sell = max(int(r.get("sell", 0)), 0) // 1000
        net  = buy - sell
        name = r.get("name", "")
        if name == "Foreign_Investor":
            hist_map[date_key]["foreign_net"] = net
        elif name == "Investment_Trust":
            hist_map[date_key]["invest_trust_net"] = net
        elif name == "Dealer_self":
            hist_map[date_key]["dealer_net"] = net

    # ── 加上收盤價 ──────────────────────────────
    price_rows = finmind_get("TaiwanStockPrice", symbol, start_10, end_date)
    price_map = {r["date"]: float(r.get("close", 0)) for r in price_rows}
    for date_key, row in hist_map.items():
        row["close"] = price_map.get(date_key, 0)

    history_rows = sorted(hist_map.values(), key=lambda x: x["date"])

    # ── 優先用 FinMind 最新一筆的 net，buy/sell 保留 T86 ──
    # FinMind 只有 net，T86 有 buy/sell/net
    # 策略：若 FinMind 最新日期 >= T86 日期，用 FinMind net 覆蓋 net，buy/sell 保留 T86
    latest_inst_date = ""
    if history_rows:
        latest_hist      = history_rows[-1]
        latest_inst_date = latest_hist["date"]
        fm_date_str      = latest_inst_date.replace("-", "")

        # 取 T86 的 buy/sell（若有的話）
        t86_fbuy  = institutional.get("foreign_buy",       0)
        t86_fsell = institutional.get("foreign_sell",      0)
        t86_itbuy = institutional.get("invest_trust_buy",  0)
        t86_itsell= institutional.get("invest_trust_sell", 0)
        t86_dbuy  = institutional.get("dealer_buy",        0)
        t86_dsell = institutional.get("dealer_sell",       0)

        institutional = {
            # net 優先用 FinMind（較新）
            "foreign_net":       latest_hist.get("foreign_net", institutional.get("foreign_net", 0)),
            "invest_trust_net":  latest_hist.get("invest_trust_net", institutional.get("invest_trust_net", 0)),
            "dealer_net":        latest_hist.get("dealer_net", institutional.get("dealer_net", 0)),
            # buy/sell 保留 T86 的值（FinMind 歷史沒有拆分）
            "foreign_buy":       t86_fbuy,
            "foreign_sell":      t86_fsell,
            "invest_trust_buy":  t86_itbuy,
            "invest_trust_sell": t86_itsell,
            "dealer_buy":        t86_dbuy,
            "dealer_sell":       t86_dsell,
        }

    # ── 3. 融資融券（FinMind）────────────────────
    margin_rows_raw = finmind_get("TaiwanStockMarginPurchaseShortSale", symbol, start_10, end_date)
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
    price_today_rows = finmind_get("TaiwanStockPrice", symbol,
                                   (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                                   end_date)
    latest_price_row = price_today_rows[-1] if price_today_rows else {}
    latest_price  = float(latest_price_row.get("close", 0))
    latest_volume = int(latest_price_row.get("Trading_Volume", 0)) // 1000

    # ── 5. 當沖率（TWSE）──────────────────────────
    day_trade_vol   = 0
    day_trade_ratio = 0.0
    for i in range(1, 6):
        d = (today - timedelta(days=i)).strftime("%Y%m%d")
        dt_url = f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date={d}&stockNo={symbol}&response=json"
        dt_data = twse_get(dt_url)
        if dt_data and dt_data.get("stat") == "OK" and dt_data.get("data"):
            last = dt_data["data"][-1]
            try:
                day_trade_vol = int(str(last[2]).replace(",","")) // 1000
                vol_total     = int(str(last[1]).replace(",","")) // 1000
                day_trade_ratio = round(day_trade_vol / vol_total * 100, 2) if vol_total > 0 else 0
            except Exception:
                pass
            break

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
    today = datetime.today()

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
