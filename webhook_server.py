from flask import Flask, request
import os
from dotenv import load_dotenv
import csv
import requests

app = Flask(__name__)
load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_id = event["source"]["userId"]
            msg = event["message"]["text"].strip()

            if msg.startswith("+"):
                symbol = msg[1:].strip()
                if add_stock_to_user_list(user_id, symbol):
                    reply_text(user_id, f"✅ 已加入追蹤：{symbol}")
                else:
                    reply_text(user_id, f"⚠️ {symbol} 已在追蹤清單中")

            elif msg.startswith("-"):
                symbol = msg[1:].strip()
                if remove_stock_from_user_list(user_id, symbol):
                    reply_text(user_id, f"❌ 已取消追蹤：{symbol}")
                else:
                    reply_text(user_id, f"⚠️ 沒有在清單中：{symbol}")

            elif msg == "/list":
                stocks = get_user_stock_list(user_id)
                if stocks:
                    text = "📋 目前追蹤清單：\n" + "\n".join(f"- {s}" for s in stocks)
                else:
                    text = "📭 清單是空的喔，請用 `+股票代碼` 加入追蹤！"
                reply_text(user_id, text)

    return "OK", 200

def get_user_stock_list(user_id):
    path = f"user_data/{user_id}.csv"
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding="utf-8") as f:
        return [row[0] for row in csv.reader(f)]

def add_stock_to_user_list(user_id, symbol):
    path = f"user_data/{user_id}.csv"
    os.makedirs("user_data", exist_ok=True)
    stocks = get_user_stock_list(user_id)
    if symbol in stocks:
        return False
    with open(path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([symbol])
    return True

def remove_stock_from_user_list(user_id, symbol):
    path = f"user_data/{user_id}.csv"
    if not os.path.exists(path):
        return False
    stocks = get_user_stock_list(user_id)
    if symbol not in stocks:
        return False
    stocks.remove(symbol)
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        for s in stocks:
            writer.writerow([s])
    return True

def reply_text(user_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
