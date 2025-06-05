# 使用官方輕量版 Python（Debian/Ubuntu 版，適合科學套件）
FROM python:3.12-slim


# 建立工作目錄
WORKDIR /app

# ---- 系統相依套件（編譯 wheel 時可能用到） ----
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc git \
    && rm -rf /var/lib/apt/lists/*

# ---- 安裝 Python 依賴 ----
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---- 複製專案程式 ----
COPY crawler.py verifier.py ./

# 預先建立輸出資料夾（避免權限問題）
RUN mkdir -p /app/output

# 預設指令：依序執行 crawler → verifier
CMD ["sh", "-c", "python crawler.py && python verifier.py"]