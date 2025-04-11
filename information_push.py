import os
from datetime import datetime, time, timedelta
import pytz
import yfinance as yf
import requests
from dotenv import load_dotenv
from db import get_all_users, list_tracked_stocks

load_dotenv()
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# 台灣時間
tz = pytz.timezone("Asia/Taipei")
now = datetime.now(tz)
current_time_str = now.strftime("%H:%M")
current_time = now.time()

# 台股開盤時間（09:00–13:30）
MARKET_OPEN = time(9, 0)
MARKET_CLOSE = time(13, 30)

# 判斷今天是否為交易日（週一～週五）
def is_trading_day():
    return now.weekday() < 5

# 傳送 LINE 訊息
def send_line_message(user_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"[{user_id}] LINE 回應：{response.status_code}")

# 計算近一個月和近一年平均價格
def get_averages(symbol):
    end = datetime.now()
    start_month = end - timedelta(days=30)
    start_year = end - timedelta(days=365)

    df = yf.download(f"{symbol}.TW", start=start_year.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)

    if df.empty or 'Close' not in df:
        return None, None

    monthly_avg = df.loc[start_month:].Close.mean()
    yearly_avg = df.Close.mean()

    return round(monthly_avg, 2), round(yearly_avg, 2)

# 根據時間傳回即時價 or 收盤價
def get_price_info(symbol):
    stock = yf.Ticker(f"{symbol}.TW")
    info = stock.info

    if current_time < MARKET_OPEN:
        return None, "❗ 尚未開市"
    elif MARKET_OPEN <= current_time <= MARKET_CLOSE:
        return info.get("regularMarketPrice"), "📈 即時價格"
    else:
        return info.get("previousClose"), "📉 收盤價"

# 計算與均價差異
def compare_price(base, current):
    if not base or base == 0:
        return "無法比較"
    change = (current - base) / base * 100
    arrow = "⬆️ 上漲" if change > 0 else "⬇️ 下跌"
    return f"{arrow} {abs(round(change, 2))}%"

# 主推播邏輯
def run_push():
    if not is_trading_day():
        print("今天休市 💤")
        return

    users = get_all_users()

    for user in users:
        user_id = user["line_user_id"]
        notify_time = user["notify_time"]

        if notify_time != current_time_str:
            continue

        symbols = list_tracked_stocks(user_id)
        if not symbols:
            continue

        messages = []

        for symbol in symbols:
            price, tag = get_price_info(symbol)
            stock = yf.Ticker(f"{symbol}.TW")
            name = stock.info.get("longName", "（未知名稱）")

            if price is None:
                messages.append(f"{symbol}：❗ 尚未開市，請設定推播時間為 09:00 後")
                continue

            month_avg, year_avg = get_averages(symbol)

            if month_avg is None:
                messages.append(f"{symbol}：無法取得平均價資料")
                continue

            msg = (
                f"📌 {symbol} {name}\n"
                f"現價：{price} 元（{tag}）\n\n"
                f"📊 價格比較\n"
                f"- 比較近1個月均價：{compare_price(month_avg, price)}\n"
                f"- 比較近1年均價：{compare_price(year_avg, price)}"
            )
            messages.append(msg)

        send_line_message(user_id, "\n\n".join(messages))
        print(f"✅ 已推播給 {user_id}")

if __name__ == "__main__":
    run_push()