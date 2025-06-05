#!/usr/bin/env python3
"""
github_game_finder.py
從 GitHub 搜尋符合條件的遊戲專案並輸出 CSV
"""

import csv
import os
import time
from datetime import datetime
from typing import List, Dict

import requests
from dotenv import load_dotenv
from urllib.parse import quote_plus

# -------------- 基本參數 ------------------
QUERY_KEYWORDS = "game unity 2d"            # 關鍵字（空白分隔 = AND）
TOPICS         = ["unity", "2d"]            # topics: unity AND 2d
LANGUAGE       = "C#"                       # 語言
MIN_STARS      = 200                        # 星數下限
PUSHED_AFTER   = "2024-12-01"               # 最後更新不得早於
LICENSES       = ["mit", "apache-2.0"]      # 授權白名單（小寫）
PER_PAGE       = 100                        # GitHub 上限
MAX_PAGES      = 10                         # 最多抓 1,000 筆
OUTPUT_FILE    = "github_games.csv"
# ------------------------------------------

API_URL = "https://api.github.com/search/repositories"
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

def build_query() -> str:
    q = []
    if QUERY_KEYWORDS:
        q.append(quote_plus(QUERY_KEYWORDS))
    for t in TOPICS:
        q.append(f"topic:{t}")
    if LANGUAGE:
        q.append(f"language:{LANGUAGE}")
    if MIN_STARS:
        q.append(f"stars:>={MIN_STARS}")
    if PUSHED_AFTER:
        q.append(f"pushed:>={PUSHED_AFTER}")
    return "+".join(q)

def fetch_page(page: int) -> Dict:
    params = {
        "q": build_query(),
        "sort": "stars",
        "order": "desc",
        "per_page": PER_PAGE,
        "page": page,
    }
    resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def filter_by_license(items) -> List[Dict]:
    if not LICENSES:
        return items
    return [
        it for it in items
        if it.get("license") and it["license"]["spdx_id"].lower() in LICENSES
    ]

def to_row(it) -> List:
    return [
        it["full_name"],
        it["html_url"],
        it["stargazers_count"],
        it["pushed_at"][:10],
        it["license"]["spdx_id"] if it.get("license") else "N/A",
    ]

def main():
    print("🔍  正在搜尋 GitHub 遊戲專案…")
    rows = []
    for page in range(1, MAX_PAGES + 1):
        data = fetch_page(page)
        items = filter_by_license(data.get("items", []))
        rows.extend([to_row(it) for it in items])
        print(f"  - 取得第 {page} 頁，共 {len(items)} 筆（累計 {len(rows)}）")
        time.sleep(1)  # 避免過度觸發速率限制
        if len(data.get("items", [])) < PER_PAGE:
            break

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["repo_name", "html_url", "stars", "last_pushed", "license"])
        writer.writerows(rows)

    print(f"✅ 完成！結果已輸出至 {OUTPUT_FILE}（{len(rows)} 筆）")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ 請先在 .env 設定 GITHUB_TOKEN")
    else:
        main()
