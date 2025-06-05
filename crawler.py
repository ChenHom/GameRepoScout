#!/usr/bin/env python3
"""
crawler.py
──────────
以多條 GitHub Search Query 取得候選遊戲專案清單，並輸出 `raw_repos.json / csv`.

‣ .env 變數一覽
    GITHUB_TOKEN        GitHub Personal Access Token（建議必填）
    QUERY_KEYWORDS      關鍵字，預設 "unity game"
    MIN_STARS           星數下限，預設 20
    TOPIC_FILTERS       topic 相關條件
    LANG_FILTER         語言條件
    DATE_FILTER         近期更新條件
    ANDROID_FILTER      Android 專案特徵 (path:/AndroidManifest.xml)
    IOS_FILTER          iOS 專案特徵 (filename:Info.plist)
    GRS_MAX_PAGES       每條 Query 最多分頁數 (REST Search 上限 10 = 1000 筆)

‣ 產出
    output/raw_repos.json
    output/raw_repos.csv
"""

from __future__ import annotations
import json, os
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# ──────────────── 基本設定 ────────────────
load_dotenv()

TOKEN   = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# 可由 .env 覆寫的查詢條件
QUERY_KEYWORDS = os.getenv("QUERY_KEYWORDS", "unity game")
MIN_STARS      = os.getenv("MIN_STARS", "20")

TOPIC_FILTERS  = os.getenv(
    "TOPIC_FILTERS",
    "",
)
LANG_FILTER    = os.getenv("LANG_FILTER", "")
DATE_FILTER    = os.getenv("DATE_FILTER", "pushed:>=2024-06-01")

ANDROID_FILTER = os.getenv("ANDROID_FILTER",  "")
IOS_FILTER     = os.getenv("IOS_FILTER",      "")

API_URL   = "https://api.github.com/search/repositories"
PER_PAGE  = 100
MAX_PAGES = int(os.getenv("GRS_MAX_PAGES", "10"))   # Search API 最多 1,000 筆

# 輸出路徑
OUTPUT_DIR = Path("output"); OUTPUT_DIR.mkdir(exist_ok=True)
RAW_JSON   = OUTPUT_DIR / "raw_repos.json"
RAW_CSV    = OUTPUT_DIR / "raw_repos.csv"

# ──────────────── 組 Query 清單 ────────────────
BASE_QUERY = (
    f"{QUERY_KEYWORDS} {TOPIC_FILTERS} {LANG_FILTER} "
    f"stars:>={MIN_STARS} {DATE_FILTER}"
)

QUERY_LIST: List[str] = []
if ANDROID_FILTER:
    QUERY_LIST.append(f"{BASE_QUERY} {ANDROID_FILTER}")
if IOS_FILTER:
    QUERY_LIST.append(f"{BASE_QUERY} {IOS_FILTER}")
if not QUERY_LIST:                             # 若兩者皆空，跑 base
    QUERY_LIST.append(BASE_QUERY)

# ──────────────── 工具函式 ────────────────
def fetch_page(q: str, page: int) -> Dict:
    params = {
        "q": q,
        "sort": "stars",
        "order": "desc",
        "per_page": PER_PAGE,
        "page": page,
    }
    resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
    print(
        f"[DEBUG] page={page} status={resp.status_code} "
        f"remaining={resp.headers.get('X-RateLimit-Remaining')}"
    )
    print(f"[DEBUG] full_url: {resp.url}")
    resp.raise_for_status()
    return resp.json()

def run_query(q: str) -> List[Dict]:
    data  = fetch_page(q, 1)
    items = data.get("items", [])
    total = min(data.get("total_count", 0), MAX_PAGES * PER_PAGE)

    if total > PER_PAGE:
        pages = min((total + PER_PAGE - 1) // PER_PAGE, MAX_PAGES)
        for p in tqdm(range(2, pages + 1), desc="paging"):
            items.extend(fetch_page(q, p).get("items", []))
    return items

# ──────────────── 主程式 ────────────────
if __name__ == "__main__":
    all_items: List[Dict] = []
    for q in QUERY_LIST:
        print(f"\n🔍  Query => {q}")
        all_items.extend(run_query(q))

    # 去重
    unique_items = {i["full_name"]: i for i in all_items}.values()
    print(f"✅  Total raw repos (dedup): {len(unique_items)}")

    # 存 JSON
    RAW_JSON.write_text(json.dumps(list(unique_items), ensure_ascii=False, indent=2))

    # 存 CSV
    df = pd.DataFrame({
        "repo_name": [r["full_name"] for r in unique_items],
        "html_url":  [r["html_url"]  for r in unique_items],
        "stars":     [r["stargazers_count"] for r in unique_items],
        "pushed_at": [r["pushed_at"][:10]   for r in unique_items],
        "license":   [(r.get("license") or {}).get("spdx_id", "N/A") for r in unique_items],
    })
    df.to_csv(RAW_CSV, index=False)
    print(f"📄  raw_repos.json / raw_repos.csv 已寫入 {OUTPUT_DIR}")
