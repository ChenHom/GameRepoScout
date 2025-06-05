# GameRepoScout

GameRepoScout 是一個用於搜尋、驗證並彙整 GitHub 上專案的自動化工具。它支援以關鍵字、星數、平台等條件搜尋，並驗證專案是否為查詢的專案，最終輸出整理好的專案清單。

## 特色

- 支援多條件搜尋（關鍵字、星數、語言、平台等）
- 自動去重、分頁抓取
- 非同步驗證專案結構是否為 Unity 專案
- 產出 JSON 與 CSV 格式的專案清單
- 可用 Docker Compose 一鍵執行

## 專案結構

```txt
GameRepoScout/
├── crawler.py           # 搜尋 GitHub 專案並產生 raw_repos.json/csv
├── verifier.py          # 驗證專案，產生 verified_repos.csv
├── requirements.txt     # Python 依賴套件
├── Dockerfile           # Docker 映像建置腳本
├── docker-compose.yml   # Docker Compose 配置
├── .env.example         # 環境變數範例
├── output/              # 輸出資料夾
│   ├── raw_repos.json
│   ├── raw_repos.csv
│   └── verified_repos.csv
```

## 快速開始

### 1. 設定環境變數

請複製 `.env.example` 為 `.env`，並填入你的 GitHub Personal Access Token：

```sh
cp .env.example .env
# 編輯 .env，填入 GITHUB_TOKEN 及查詢條件
```

### 2. 使用 Docker Compose 執行

```sh
docker compose up --build
```

執行完畢後，結果會輸出在 `output/` 資料夾。

### 3. 手動執行（本機 Python）

安裝依賴：

```sh
pip install -r requirements.txt
```

執行 crawler 與 verifier：

```sh
python crawler.py
python verifier.py
```

## 主要環境變數說明

- `GITHUB_TOKEN`：GitHub Personal Access Token（建議必填，否則易受 API 限制）
- `QUERY_KEYWORDS`：搜尋關鍵字
- `MIN_STARS`：最小星數
- `ANDROID_FILTER`、`IOS_FILTER`：平台過濾條件

更多條件請參考 `.env.example`。

## 產出說明

- `output/raw_repos.json`：原始搜尋結果（去重複）
- `output/raw_repos.csv`：原始搜尋結果（CSV）
- `output/verified_repos.csv`：通過驗證的專案清單

## 授權

MIT License
