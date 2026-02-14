# Python 3.12をベースイメージとして使用
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをすべてコピー
COPY . .

# ベクトル化済みのchroma_dbをイメージに含める
COPY data/chroma_db ./data/chroma_db

# Streamlitのポート8080を公開
EXPOSE 8080

# Streamlitアプリを起動
CMD ["streamlit", "run", "main.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]