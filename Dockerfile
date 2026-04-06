FROM python:3.12-slim

WORKDIR /app

# 依存関係のインストール（キャッシュ活用のためrequirements.txtを先にコピー）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

CMD ["python", "main.py"]
