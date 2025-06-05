#!/usr/bin/env python3
"""verifier.py – 非同步驗證 raw_repos.json 中的候選是否為可執行 Unity 專案"""

from __future__ import annotations
import asyncio, json, os, re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import aiohttp, pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# ───────────── 設定 ─────────────
load_dotenv()
TOKEN   = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
CONCURRENCY = int(os.getenv("GRS_VERIFY_CONCURRENCY", "25"))

OUTPUT_DIR   = Path("output")
RAW_JSON     = OUTPUT_DIR / "raw_repos.json"
VERIFIED_CSV = OUTPUT_DIR / "verified_repos.csv"
TREE_URL     = "https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"

# ───────────── Heuristics ─────────────
UNITY_RULES = [
    re.compile(r"^Assets/"),
    re.compile(r"^ProjectSettings/ProjectSettings\.asset$"),
    re.compile(r"^Packages/manifest\.json$"),
]

def is_unity_game(tree_json: Dict) -> bool:
    if not tree_json or "tree" not in tree_json:
        return False
    paths = {t["path"] for t in tree_json["tree"]}
    return all(any(rx.match(p) for p in paths) for rx in UNITY_RULES)

# ───────────── 非同步 I/O ─────────────
async def fetch_tree(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    full_name: str,
) -> Tuple[str, Optional[Dict]]:
    owner, repo = full_name.split("/")
    url = TREE_URL.format(owner=owner, repo=repo)
    async with sem:            # 併發上限
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return full_name, None
                return full_name, await resp.json()
        except aiohttp.ClientError:
            return full_name, None

async def verify_all(repos: List[Dict]) -> List[Dict]:
    ok: List[Dict] = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        coros = [fetch_tree(session, sem, r["full_name"]) for r in repos]

        # 逐一等待完成，確保在 session 關閉前全部處理
        results = []
        for fut in tqdm(asyncio.as_completed(coros), total=len(coros), desc="Verifying"):
            results.append(await fut)

    # 收斂結果
    for full_name, tree_json in results:
        if tree_json and is_unity_game(tree_json):
            ok.append(next(r for r in repos if r["full_name"] == full_name))
    return ok

# ───────────── main ─────────────
if __name__ == "__main__":
    if not RAW_JSON.exists():
        raise SystemExit("❌  找不到 raw_repos.json，請先執行 crawler.py")

    repos: List[Dict] = json.loads(RAW_JSON.read_text("utf-8"))
    print(f"🔍  待驗證 repo 數量：{len(repos)}  (concurrency={CONCURRENCY})")

    verified = asyncio.run(verify_all(repos))
    print(f"✅  通過驗證：{len(verified)}")

    df = pd.DataFrame({
        "repo_name": [r["full_name"] for r in verified],
        "html_url":  [r["html_url"]  for r in verified],
        "stars":     [r["stargazers_count"] for r in verified],
        "pushed_at": [r["pushed_at"][:10] for r in verified],
        "license":   [(r.get("license") or {}).get("spdx_id", "N/A") for r in verified],
    })
    df.to_csv(VERIFIED_CSV, index=False)
    print(f"📄  verified_repos.csv 已寫入 {VERIFIED_CSV}")
