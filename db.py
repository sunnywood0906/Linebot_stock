import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 載入 .env 裡的設定
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# 建立連線
def get_conn():
    #print("目前讀到的 DATABASE_URL：", os.getenv("DATABASE_URL"))
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# 新增使用者（如果不存在）
def add_user_if_not_exist(line_user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE line_user_id = %s", (line_user_id,))
    result = cur.fetchone()
    if not result:
        cur.execute("INSERT INTO users (line_user_id) VALUES (%s)", (line_user_id,))
        conn.commit()
    cur.close()
    conn.close()

# 取得使用者 ID
def get_user_id(line_user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE line_user_id = %s", (line_user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user["id"] if user else None

# 加入追蹤股票（最多 20 檔）
def add_tracked_stock(line_user_id, symbol):
    add_user_if_not_exist(line_user_id)
    user_id = get_user_id(line_user_id)

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM tracked_stocks WHERE user_id = %s AND symbol = %s", (user_id, symbol))
    if cur.fetchone():
        msg = f"⚠️ 你已經追蹤過 {symbol}"
    else:
        cur.execute("SELECT COUNT(*) FROM tracked_stocks WHERE user_id = %s", (user_id,))
        count = cur.fetchone()["count"]
        if count >= 20:
            msg = "⚠️ 每位使用者最多只能追蹤 20 檔股票"
        else:
            cur.execute("INSERT INTO tracked_stocks (user_id, symbol) VALUES (%s, %s)", (user_id, symbol))
            conn.commit()
            msg = f"✅ 成功加入追蹤：{symbol}"

    cur.close()
    conn.close()
    return msg

# 移除追蹤
def remove_tracked_stock(line_user_id, symbol):
    user_id = get_user_id(line_user_id)
    if not user_id:
        return "❌ 使用者不存在"

    conn = get_conn()
    cur = conn.cursor()
    # 檢查是否真的有追蹤該股票
    cur.execute("SELECT 1 FROM tracked_stocks WHERE user_id = %s AND symbol = %s", (user_id, symbol))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return f"⚠️ 你本來就沒有追蹤 {symbol}或是你已取消追蹤"
    # 執行刪除
    cur.execute("DELETE FROM tracked_stocks WHERE user_id = %s AND symbol = %s", (user_id, symbol))
    conn.commit()
    cur.close()
    conn.close()
    return f"🗑️ 已取消追蹤：{symbol}"

# 查詢使用者的追蹤清單
def list_tracked_stocks(line_user_id):
    user_id = get_user_id(line_user_id)
    if not user_id:
        return []

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT symbol FROM tracked_stocks WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row["symbol"] for row in rows]

def update_notify_time(line_user_id, notify_time):
    add_user_if_not_exist(line_user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET notify_time = %s
        WHERE line_user_id = %s
    """, (notify_time, line_user_id))
    conn.commit()
    cur.close()
    conn.close()

# 取得使用者的推播時間
def get_notify_time(line_user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT notify_time FROM users WHERE line_user_id = %s", (line_user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["notify_time"] if row and row["notify_time"] else None

def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT line_user_id, notify_time FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users
