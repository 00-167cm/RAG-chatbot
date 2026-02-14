# 🤖 RAG Chatbot

## 🔗 各種リンク(アプリケーションURL・参考資料)

- **[RAG Chatbot デモサイト](https://rag-chatbot-787511911100.asia-northeast1.run.app/)**
  - _※ 日次でデータを自動リセットしています。質問などご自由にお試しください。_
  - _※ コールドスタートのため初回起動の際は時間がかかります。_
- **[ユーザーガイド](https://www.notion.so/307d5e28de6980b39635ef0226c1dc01?source=copy_link)**
- **[Googleドライブ（RAG使用資料）](https://drive.google.com/drive/folders/1uBGYifqCWblvLONPyNNK-RdFmYNZD296?usp=sharing)**
- **[システムフロー図](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&target=self&highlight=0000ff&edit=_blank&layers=1&nav=1&title=%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%83%95%E3%83%AD%E3%83%BC%E5%9B%B3&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D1ofEfPXRgYD6ISPqPC8mwLVyPSQCLdcGO%26export%3Ddownload#%7B%22pageId%22%3A%225w3JKShJVbbiZiXe1k3E%22%7D)**
- **[アーキテクチャ図](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&target=blank&highlight=0000ff&edit=_blank&layers=1&nav=1&title=%E3%82%A2%E3%83%BC%E3%82%AD%E3%83%86%E3%82%AF%E3%83%81%E3%83%A3%E5%9B%B3&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D1sH6jKtMhl_M5Q7e2QC67yehbxfk3qdST%26export%3Ddownload)**

---

## 📖 プロジェクト概要

金融業界の審査業務における「膨大かつ複雑な規定集から情報が見つけにくい」という検索コストの課題の解決を想定し**、設計・開発した**RAGチャットボットです。

---

## ✨ 機能一覧

本アプリケーションには、実務利用を想定した以下の機能が実装されています。

| 分類            | 機能名                   | 技術的な実装ポイント                                                                                                     |
| --------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| **🤖 RAG**      | **質問の自動振り分け**   | ユーザーの質問が「規定に関するもの」か「雑談」かを判別し、RAG検索を行うか通常AIで返すかを動的に振り分けます。            |
|                 | **参照元の明示**         | 回答に使用したドキュメント名、該当ページ数、および参照元の Google Drive リンクをUI上に明示し、情報の透明性を担保します。 |
| **💻 UX**       | **ストリーミング応答**   | 回答生成を待つことなく、トークン生成ごとに逐次テキストを表示することで、体感待ち時間を極小化します。                     |
|                 | **タイトルの自動生成**   | 初回のやり取り完了後にバックグラウンドで会話内容を要約し、サイドバーの履歴タイトルを自動的に生成します。                 |
| **⚙️ システム** | **会話文脈の永続化**     | Firestore をバックエンドに使用し、ブラウザのリロードやセッション切れが発生しても、直前の文脈を完全に復元します。         |
|                 | **起動プロセスの高速化** | DB接続やモデルロードなどの重い初期化処理をキャッシュし、2回目以降の動作を高速化します。                                  |
|                 | **デモデータの自動復旧** | デモ環境の健全性を保つため、毎日定時にデータをリセットし、テンプレートデータを再投入するバッチ処理を稼働させています。   |

---

## 📁 ファイル構成と役割

```
.
├── main.py                    【起動】 アプリケーションの起動と初期化
├── gui.py                     【画面】 チャット画面の表示と入力受付
├── chat_manager.py            【制御】 会話履歴の管理とデータの橋渡し
├── langchain_manager.py       【AI】 OpenAI APIとの連携、プロンプト管理
├── db_manager.py              【データ】 Firestoreへの読み書き
├── rag_manager.py             【RAG】 RAGモードの判定と資料検索の統合
├── chroma_manager.py          【検索】 ChromaDBへの検索・登録
├── document_processor.py      【前処理】 PDFのテキスト化と分割処理
├── reload_documents.py        【バッチ】 資料の再読み込みスクリプト
├── config/
│   └── settings.py            【設定】 全設定値の一元管理
├── data/
│   ├── documents/             【資料】 学習元のPDF・HTML
│   └── chroma_db/             【DB】 ベクトルデータベースの永続化先
├── requirements.txt           【依存】 必要なライブラリ一覧
├── Dockerfile                 【Docker】 コンテナ化設定
└── db_initializer.py　　　　　　【バッチ】 毎日22時に実行されるデータリセット処理
```

---

## 🏷️ データベース構造

### Firestore データ階層

```
chats (コレクション)
 └── {chat_id} (ドキュメント)
      ├── title: "収入証明書について"
      ├── created_at: 2025-02-08T10:00:00+09:00
      ├── updated_at: 2025-02-08T10:05:00+09:00
      └── messages: [配列]
           ├── [0]
           │    ├── role: "user"
           │    ├── content: "収入証明書の有効期限は？"
           │    └── created_at: 2025-02-08T10:00:00+09:00
           │
           └── [1]
                ├── role: "assistant"
                ├── content: "NSC業務フローに基づき、収入証明書の有効期限は..."
                ├── is_rag: true
                ├── created_at: 2025-02-08T10:00:05+09:00
                └── chunks: [配列]
                     ├── [0]
                     │    ├── chunk_id: "収入証明書確認ルール集.pdf_5_2"
                     │    ├── distance: 0.85（ベクトル距離：数値が小さいほど類似）
                     │    └── source: "収入証明書確認ルール集.pdf"
                     │
                     └── [1]
                          ├── chunk_id: "収入証明書確認ルール集.pdf_5_3"
                          ├── distance: 0.92
                          └── source: "収入証明書確認ルール集.pdf"
```

### データ設計のポイント

1. **配列構造を採用**：サブコレクションではなく、配列内にメッセージを格納することで、1回のクエリで全履歴を取得可能
2. **RAG情報の保存**：どの資料を参照したかを`chunks`配列で記録し、後から検証可能
3. **日本時間で統一**：すべてのタイムスタンプをJST（UTC+9）で保存

---

## ⚙️ 設定パラメータ

### RAG関連の設定値

| 設定項目                                    | 型    | 初期値 | 説明                                |
| ------------------------------------------- | ----- | ------ | ----------------------------------- |
| **閾値（RAG_THRESHOLD）**                   | float | 1.2    | この値以下の類似度でRAGモードを発動 |
| 範囲：0~2.0　                               |
| **取得件数（TOP_K_RESULTS）**               | int   | 3      | 類似度の高い資料を上位3件取得       |
| **チャンクサイズ（CHUNK_SIZE）**            | int   | 500    | 資料を500文字ごとに分割             |
| **チャンクオーバーラップ（CHUNK_OVERLAP）** | int   | 100    | 分割時に前後100文字ずつ重複させる   |

**RAG判定の閾値設定：**

- **デフォルト値：1.2**
- **調整可能範囲：0.0〜2.0**
- **推奨値：1.0〜1.5**

**閾値の意味：**

- OpenAI Embeddingsで生成されたベクトル間のL2距離を表す
- 0に近いほど意味が近く、2.0を超えるとほぼ無関係
- 実用上、2.0以上の距離では資料の関連性がほぼゼロになるため、上限を2.0に設定

---

## AI関連の設定値

| 設定項目                               | 型    | 初期値                   | 説明                                     |
| -------------------------------------- | ----- | ------------------------ | ---------------------------------------- |
| **AIモデル（OPENAI_MODEL）**           | str   | "gpt-4o-mini"            | 回答生成に使用するモデル                 |
| **Embeddingモデル（EMBEDDING_MODEL）** | str   | "text-embedding-3-small" | テキストのベクトル化に使用               |
| **Temperature（TEMPERATURE）**         | float | 0.1                      | AIの応答の多様性（低いほど一貫性が高い） |

---

## その他の設定値

| 設定項目                                   | 型       | 初期値 | 説明                         |
| ------------------------------------------ | -------- | ------ | ---------------------------- |
| **タイトル最大文字数（TITLE_MAX_LENGTH）** | int      | 15     | 自動生成されるタイトルの上限 |
| **タイムゾーン（JST）**                    | timezone | UTC+9  | 日本標準時で統一             |

## 🛠 技術スタック

### プログラミング言語・フレームワーク

| 技術                         | バージョン | 用途                    |
| ---------------------------- | ---------- | ----------------------- |
| **Python**                   | 3.12       | バックエンド開発        |
| **Streamlit**                | 1.51.0     | Webアプリケーション構築 |
| **LangChain**                | 1.1.0      | AI処理のフレームワーク  |
| **LangChain OpenAI**         | 1.1.0      | OpenAI統合              |
| **LangChain Text Splitters** | 1.0.0      | テキスト分割            |
| **LangChain Chroma**         | 1.0.0      | ChromaDB統合            |
| **LangChain Community**      | 0.4.1      | コミュニティツール      |

### AI・Embeddings

| 技術         | バージョン | 用途                 |
| ------------ | ---------- | -------------------- |
| **OpenAI**   | 2.8.1      | 回答生成・Embeddings |
| **ChromaDB** | 1.3.5      | ベクトルデータベース |

### インフラ・データベース

| 技術                       | バージョン  | 用途                           |
| -------------------------- | ----------- | ------------------------------ |
| **Firebase Admin SDK**     | 7.1.0       | Firestore操作                  |
| **Google Cloud Run**       | -           | アプリケーションのホスティング |
| **Google Cloud Functions** | -           | 定期バッチ処理                 |
| **Google Cloud Scheduler** | -           | バッチ処理のスケジューリング   |
| **Functions Framework**    | 3.0（推定） | Cloud Functions開発用          |
| **Docker**                 | -           | コンテナ化                     |

### データ処理・ユーティリティ

| ライブラリ         | バージョン | 用途             |
| ------------------ | ---------- | ---------------- |
| **PyMuPDF**        | 1.26.6     | PDFテキスト抽出  |
| **BeautifulSoup4** | 4.14.2     | HTMLテキスト抽出 |
| **python-dotenv**  | 1.2.1      | 環境変数管理     |
| **shortuuid**      | 1.0.13     | チャットID生成   |

# 🚀 環境構築と実行

## 📋 前提条件

- **Python 3.12**
- **OpenAI API Key**
- **Firebase認証ファイル** (`firebase-key.json`)

---

## 環境構築の2つの方法

本アプリケーションは以下2つの方法で実行できます。

1. **ローカル環境** - 自分のPC上に直接環境を構築
2. **Docker** - コンテナ環境で実行

---

## 1. ローカル環境で実行する場合

### ① リポジトリをクローン

`git clone https://github.com/your-repo/rag-chatbot.git
cd rag-chatbot`

### ② 仮想環境を作成

`python -m venv venv`

### ③ 仮想環境を有効化

**Mac/Linux:**

`source venv/bin/activate`

**Windows:**

`venv\Scripts\activate`

### ④ 依存ライブラリをインストール

`pip install -r requirements.txt

````

### ② 環境変数を設定

`プロジェクトルートに `.env` ファイルを作成し、以下を記述：
```
OPENAI_API_KEY="sk-..."`

Firebase認証ファイル `firebase-key.json` もプロジェクトルートに配置してください。

### ⑥ アプリケーションを起動

`streamlit run main.py`

ブラウザで自動的に開きます。

---

## 2. Dockerで実行する場合

### ① リポジトリをクローン

`git clone https://github.com/your-repo/rag-chatbot.git
cd rag-chatbot
````

### ② 環境変数を設定

`プロジェクトルートに `.env` ファイルを作成し、以下を記述：

````
OPENAI_API_KEY="sk-..."`

Firebase認証ファイル `firebase-key.json` もプロジェクトルートに配置してください。

### ③ Dockerイメージをビルド

`docker build -t rag-chatbot .`

このステップで仮想環境の作成とライブラリのインストールが自動で実行されます。

### ④ コンテナを起動

`docker run -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/firebase-key.json:/app/firebase-key.json \
  rag-chatbot`

ブラウザで `http://localhost:8080` にアクセスしてください。

## **コマンド一覧**

**ローカル環境**

```jsx
git clone https://github.com/your-repo/rag-chatbot.git
cd rag-chatbot
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
# .envファイルとfirebase-key.jsonを配置
streamlit run main.py
````

**Docker**

```jsx
git clone https://github.com/your-repo/rag-chatbot.git
cd rag-chatbot
# .envファイルとfirebase-key.jsonを配置
docker build -t rag-chatbot .
docker run -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/firebase-key.json:/app/firebase-key.json \
  rag-chatbot
```
