from flask import Flask, request
import os
import requests
import re 
from dotenv import load_dotenv
from db import (
    add_tracked_stock,
    remove_tracked_stock,
    list_tracked_stocks,
    update_notify_time,
    get_notify_time,
)

app = Flask(__name__)
load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            line_user_id = event["source"]["userId"]
            msg = event["message"]["text"].strip()

            # 加入股票追蹤
            if msg.startswith("+"):
                symbol = msg[1:].strip()
                reply = add_tracked_stock(line_user_id, symbol)
                reply_text(line_user_id, reply)

            # 取消追蹤
            elif msg.startswith("-"):
                symbol = msg[1:].strip()
                reply = remove_tracked_stock(line_user_id, symbol)
                reply_text(line_user_id, reply)

            # 查看追蹤清單
            elif msg == "/list":
                stocks = list_tracked_stocks(line_user_id)
                if stocks:
                    text = "📋 目前追蹤清單：\n" + "\n".join(f"- {s}" for s in stocks)
                else:
                    text = "📭 清單是空的喔，請用 `+股票代碼` 加入追蹤！"
                reply_text(line_user_id, text)

            # ✅ 設定推播時間（含格式驗證）
            elif msg.startswith("/settime"):
                try:
                    time_str = msg.split(" ", 1)[1].strip()
                    if not re.match(r"^\d{2}:\d{2}$", time_str):
                        raise ValueError()
                    update_notify_time(line_user_id, time_str)
                    reply_text(line_user_id, f"✅ 已設定推播時間為 {time_str}")
                except:
                    reply_text(line_user_id, "❌ 格式錯誤，請用 `/settime HH:MM`（例如：08:30）")

            # 查詢目前的推播時間
            elif msg == "/time":
                t = get_notify_time(line_user_id)
                if t:
                    reply_text(line_user_id, f"⏰ 你目前設定的推播時間是 {t}")
                else:
                    reply_text(line_user_id, "你尚未設定推播時間，可以用 `/settime 08:00` 設定喔！")

    return "OK", 200

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
    res = requests.post(url, headers=headers, json=data)
    print(f"[LINE 推播] 狀態碼：{res.status_code}，回傳內容：{res.text}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)