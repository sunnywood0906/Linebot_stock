from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import csv
#hw3
from stock_list import load_stocks
CSV_FILE = "tracked_stocks.csv"

# 讀取 .env 檔案
load_dotenv()
stocks = load_stocks()

# 🧾 讀取 CSV 裡的 symbol 欄位
def load_symbols_from_csv(csv_path="tracked_stocks.csv"):
    symbols = []
    with open(csv_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row["symbol"].strip()
            if symbol:
                symbols.append(symbol)
    return symbols

symbols = load_symbols_from_csv()
print("載入的 symbol 清單：", symbols)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # 顯示瀏覽器
    page = browser.new_page()

    print("啟動瀏覽器")

    for symbol in symbols:
        print(f"🚀 正在處理：{symbol}")
        url = f"https://tw.stock.yahoo.com/quote/{symbol}.TW"
        page.goto(url)
        page.wait_for_timeout(3000)

        try:
            price = page.locator("span[class*='Fz(32px)']").inner_text()
            print(f"{symbol} 現價：{price} 元")
        except Exception as e:
            print(f"{symbol} 擷取失敗：{e}")

    # 保持瀏覽器開啟，方便 Debug
    input("瀏覽器保持開啟，按 Enter 關閉...")

    # 關閉瀏覽器
    browser.close()
    print("瀏覽器已關閉")