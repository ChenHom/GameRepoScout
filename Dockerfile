# 使用官方輕量版 Python 映像
FROM python:alpine

# 建立工作目錄
WORKDIR /app

# 複製依賴檔並先行安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案程式
COPY github_game_finder.py .

# 預設執行指令（亦可在 docker-compose 中覆寫）
CMD ["python", "github_game_finder.py"]
