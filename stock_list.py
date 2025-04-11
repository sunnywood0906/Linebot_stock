import csv
import os

CSV_FILE = "tracked_stocks.csv"

def load_stocks():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, newline='', encoding="utf-8") as f:
        return list(csv.DictReader(f))

def add_stock(symbol, name, target_price):
    stocks = load_stocks()
    stocks.append({"symbol": symbol, "name": name, "target_price": target_price})
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["symbol", "name", "target_price"])
        writer.writeheader()
        for s in stocks:
            writer.writerow(s)