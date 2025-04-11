import os
from dotenv import load_dotenv
import csv
import yfinance as yf
import requests

# 讀取 .env
load_dotenv()
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(user_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"推播狀態碼：{response.status_code}")
    print(f"回傳內容：{response.text}")

def load_tracked_stocks(path="tracked_stocks.csv"):
    with open(path, newline='', encoding="utf-8") as f:
        return list(csv.DictReader(f))

def get_price(symbol):
    stock = yf.Ticker(f"{symbol}.TW")
    return stock.info["regularMarketPrice"]

if __name__ == "__main__":
    stocks = load_tracked_stocks()
    messages = []

    for stock in stocks:
        symbol = stock["symbol"]
        name = stock["name"]
        target = float(stock["target_price"])
        price = get_price(symbol)

        print(f"{symbol} 現價：{price} 元（目標：{target} 元）")

        messages.append(f"{name}（{symbol}）：{price} 元")

    # 組合訊息，每天一次推播
    full_message = "📈 每日股價追蹤報告\n" + "\n".join(messages)
    send_line_message(USER_ID, full_message)