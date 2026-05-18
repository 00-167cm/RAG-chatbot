# 🤖 RAG Chatbot

## 🔗 各種リンク

### アプリケーションURL

- [**RAG Chatbot デモサイト**](https://rag-chatbot-787511911100.asia-northeast1.run.app/)
    - *※ 日次で会話履歴をを自動リセットしています(22時)。質問などご自由にお試しください。*
    - *※ コールドスタートのため初回起動の際は時間がかかります。*
- [**GoogleDrive（RAG参照資料）**](https://drive.google.com/drive/folders/1a9DW1Bnh4BPOADqiTkyyu7LEJXPCgJAk?usp=sharing)
- [**システム説明書**](https://www.notion.so/364d5e28de698089bf2bee4658b5702e?pvs=21)
- [**システムフロー図**](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&target=self&highlight=0000ff&edit=_blank&layers=1&nav=1&title=%E3%82%B7%E3%82%B9%E3%83%86%E3%83%A0%E3%83%95%E3%83%AD%E3%83%BC%E5%9B%B3&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D1ofEfPXRgYD6ISPqPC8mwLVyPSQCLdcGO%26export%3Ddownload#%7B%22pageId%22%3A%225w3JKShJVbbiZiXe1k3E%22%7D)
- [**アーキテクチャ図**](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&target=blank&highlight=0000ff&edit=_blank&layers=1&nav=1&title=%E3%82%A2%E3%83%BC%E3%82%AD%E3%83%86%E3%82%AF%E3%83%81%E3%83%A3%E5%9B%B3&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D1sH6jKtMhl_M5Q7e2QC67yehbxfk3qdST%26export%3Ddownload)

---

## ✨ 機能一覧

本アプリケーションには、実務利用を想定した以下の機能が実装されています。

| 分類 | 機能名 | 技術的な実装ポイント |
| --- | --- | --- |
| **🤖 RAG** | **質問の自動振分け** | ユーザーの質問が「規定に関するもの」か「雑談」かを判別し、RAG検索を行うか通常AIで返すかを動的に振り分けます。 |
|  | **参照元の明示** | 回答に使用したドキュメント名、該当ページ数、および参照元の Google ドライブ リンク(Googleドライブを参照元にした場合)をUI上に明示し、情報の透明性を担保します。 |
|  | **画像PDFのOCR対応** | テキスト埋め込みのないPDFを自動検知し、Tesseract OCRでフォールバック抽出します。 |
|  | **複数ファイル形式の対応** | PDF、HTML、Excel(.xlsx)、Word(.docx)、PowerPoint(.pptx) の5形式に対応。Google ドライブ上のスプレッドシート・ドキュメント・スライドも自動でOffice形式に変換して取り込みます。 |
| **💻 UX** | **ストリーミング応答** | 回答生成を待つことなく、トークン生成ごとに逐次テキストを表示することで、体感待ち時間を極小化します。 |
|  | **タイトルの自動生成** | 初回のやり取り完了後にバックグラウンドで会話内容を要約し、サイドバーの履歴タイトルを自動的に生成します。 |
| **⚙️ システム** | **会話文脈の永続化** | Firestoreをバックエンドに使用し、ブラウザのリロードやセッション切れが発生しても、直前の文脈を完全に復元します。 |
|  | **起動プロセスの高速化** | DB接続やモデルロードなどの重い初期化処理をキャッシュし、2回目以降の動作を高速化します。 |
|  | **デモデータの自動復旧** | デモ環境の健全性を保つため、毎日定時にデータをリセットし、テンプレートデータを再投入するバッチ処理を稼働させています。 |
|  | **資料取込元の切替** | `settings.py` の `DOC_SOURCE` を `"local"` / `"gd"` に変更するだけで、ローカルフォルダとGoogle Driveを切り替え可能です。 |

---

## 📂 対応ファイル形式

---

| 元形式 | 取込形式 | 処理概要 |
| --- | --- | --- |
| .pdf | .pdf | PyMuPDFでテキスト抽出。抽出不可の場合はTesseract OCRにフォールバック |
| .html | .html | BeautifulSoupでテキスト抽出 |
| .xlsx | .xlsx | openpyxlで全シート・全セルを読み取り |
| .xlsm | 〃 | openpyxlで全シート・全セルを読み取り（マクロのコードは抽出対象外） |
| Googleスプレッドシート | 〃 | export_media()で.xlsxに変換後、openpyxlで処理 |
| .docx | .docx | python-docxで段落・表を抽出 |
| Googleドキュメント | 〃 | export_media()で.docxに変換後、python-docxで処理 |
| .pptx | .pptx | python-pptxでスライドごとにテキスト抽出 |
| Googleスライド | 〃 | export_media()で.pptxに変換後、python-pptxで処理 |

> 上記以外の形式（.csv、.txt、画像ファイル等）は現在未対応です。対応形式外のファイルはスキップされます。
> 

---

## 📁 ディレクトリ構成と役割

```
.
├── main.py                        【起動】 アプリケーションの起動と初期化
├── chat/
│   ├── gui.py                     【画面】 チャット画面の表示と入力受付
│   ├── chat_manager.py            【制御】 会話履歴の管理とデータの橋渡し
│   └── langchain_manager.py       【AI】   OpenAI APIとの連携、プロンプト管理
├── infrastructure/
│   ├── db_manager.py              【データ】 Firestoreへの読み書き
│   ├── rag_manager.py             【RAG】  RAGモードの判定と資料検索の統合
│   ├── chroma_manager.py          【検索】 ChromaDBへの検索・登録
│   ├── document_processor.py      【前処理】 各種ファイルのテキスト化・OCR・分割処理
│   └── google_drive_vectorizer.py 【取込】 Google Driveからの資料取り込み
├── config/
│   └── settings.py                【設定】 全設定値の一元管理
├── functions/
│   ├── main.py                    【バッチ】 毎日22時に実行されるデータリセット処理
│   └── requirements.txt           【依存】 Cloud Functions用の依存ライブラリ
├── data/
│   ├── documents/                 【資料】 学習元のドキュメント
│   └── chroma_db/                 【DB】   ベクトルデータベースの永続化先
├── secrets/
│   ├── firebase-key.json          【認証】 Firebase認証ファイル
│   └── gc_service_account.json    【認証】 Google Drive API用サービスアカウント
├── requirements.txt               【依存】 必要なライブラリ一覧
├── Dockerfile                     【Docker】 コンテナ化設定
└── .env                           【環境】 環境変数（API Keyなど）
```

[アーキテクチャ図はこちら](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&target=blank&highlight=0000ff&edit=_blank&layers=1&nav=1&title=%E3%82%A2%E3%83%BC%E3%82%AD%E3%83%86%E3%82%AF%E3%83%81%E3%83%A3%E5%9B%B3&dark=auto#Uhttps%3A%2F%2Fdrive.google.com%2Fuc%3Fid%3D1sH6jKtMhl_M5Q7e2QC67yehbxfk3qdST%26export%3Ddownload#%7B%22pageId%22%3A%22YJnWJ1LZHdyNh0J4FVVR%22%7D)

---

## 🏷️ データベース構造

### Firestore データ階層

```
chats (コレクション)
└── {chat_id} (ドキュメント)
    ├── title: "収入証明書について"
    ├── created_at: 2025-02-08T10:00:00+09:00
    ├── updated_at: 2025-02-08T10:05:00+09:00
    └── messages: [配列]
        ├── [0]
        │   ├── role: "user"
        │   ├── content: "収入証明書の有効期限は？"
        │   └── created_at: 2025-02-08T10:00:00+09:00
        └── [1]
            ├── role: "assistant"
            ├── content: "参照資料に基づき..."
            ├── is_rag: true
            ├── created_at: 2025-02-08T10:00:05+09:00
            └── chunks: [配列]
                ├── [0]
                │   ├── chunk_id: "審査手順(収入証明書).pdf_5_2"
                │   ├── distance: 0.85
                │   └── source: "審査手順(収入証明書).pdf"
                └── [1]
                    ├── chunk_id: "審査手順(収入証明書).pdf_5_3"
                    ├── distance: 0.92
                    └── source: "審査手順(収入証明書).pdf"
```

### データ設計のポイント

1. **配列構造を採用**：サブコレクションではなく、配列内にメッセージを格納することで、1回のクエリで全履歴を取得可能
2. **RAG情報の保存**：どの資料を参照したかを`chunks`配列で記録し、後から検証可能
3. **日本時間で統一**：すべてのタイムスタンプをJST（UTC+9）で保存

---

## ⚙️ 設定パラメータ

### RAG関連の設定値

| 設定項目 | 型 | 初期値 | 説明 |
| --- | --- | --- | --- |
| **閾値（RAG_THRESHOLD）** | float | 1.2 | この値以下の類似度でRAGモードを発動（範囲：0〜2.0） |
| **取得件数（TOP_K_RESULTS）** | int | 3 | 類似度の高い資料を上位3件取得 |
| **チャンクサイズ（CHUNK_SIZE）** | int | 500 | 資料を500文字ごとに分割 |
| **チャンクオーバーラップ（CHUNK_OVERLAP）** | int | 100 | 分割時に前後100文字ずつ重複させる |
| **資料取込元（DOC_SOURCE）** | str | "local" | ※"local": ローカルフォルダ / "gd": Google Drive |

※ 資料の取り込み元はローカルフォルダとGoogle Driveで切り替え可能です。公開中のアプリではGoogle Driveを使用しています。

### AI関連の設定値

| 設定項目 | 型 | 初期値 | 説明 |
| --- | --- | --- | --- |
| **AIモデル（OPENAI_MODEL）** | str | "gpt-4o-mini" | 回答生成に使用するモデル |
| **Embeddingモデル（EMBEDDING_MODEL）** | str | "text-embedding-3-small" | テキストのベクトル化に使用 |
| **Temperature（TEMPERATURE）** | float | 0.1 | AIの応答の多様性（低いほど一貫性が高い） |

### その他の設定値

| 設定項目 | 型 | 初期値 | 説明 |
| --- | --- | --- | --- |
| **タイトル最大文字数（TITLE_MAX_LENGTH）** | int | 15 | 自動生成されるタイトルの上限 |
| **タイムゾーン（JST）** | timezone | UTC+9 | 日本標準時で統一 |

---

## 🛠 技術スタック

### プログラミング言語・フレームワーク

| 技術 | バージョン | 用途 |
| --- | --- | --- |
| **Python** | 3.12 | バックエンド開発 |
| **Streamlit** | 1.51.0 | Webアプリケーション構築 |
| **LangChain** | 1.1.0 | AI処理のフレームワーク |
| **LangChain OpenAI** | 1.1.0 | OpenAI統合 |
| **LangChain Text Splitters** | 1.0.0 | テキスト分割 |
| **LangChain Chroma** | 1.0.0 | ChromaDB統合 |
| **GitHub Actions** | -  | CI/CD（自動ビルド・自動デプロイ） |

### AI・Embeddings

| 技術 | バージョン | 用途 |
| --- | --- | --- |
| **OpenAI** | 2.8.1 | 回答生成・Embeddings |
| **ChromaDB** | 1.3.5 | ベクトルデータベース |

### インフラ・データベース

| 技術 | バージョン | 用途 |
| --- | --- | --- |
| **Firebase Admin SDK** | 7.1.0 | Firestore操作 |
| **Google Cloud Run** | - | アプリケーションのホスティング |
| **Google Cloud Functions** | - | 定期バッチ処理 |
| **Google Cloud Scheduler** | - | バッチ処理のスケジューリング |
| **Docker** | - | コンテナ化 |

### その他ライブラリ

| ライブラリ | バージョン | 用途 |
| --- | --- | --- |
| **PyMuPDF** | 1.26.6 | PDFテキスト抽出 |
| **Tesseract OCR** | 5.5.2 | 画像PDFからのOCRテキスト抽出（システム依存） |
| **pytesseract** | 0.3.13 | Tesseract OCRのPythonラッパー |
| **pdf2image** | 1.17.0 | PDF→画像変換（OCR前処理） |
| **Poppler** | 26.02.0 | PDF画像変換エンジン（システム依存） |
| **BeautifulSoup4** | 4.14.2 | HTMLテキスト抽出 |
| **openpyxl** | 3.1.5 | Excelテキスト抽出 |
| **python-docx** | 1.2.0 | Wordテキスト抽出 |
| **python-pptx** | 1.0.2 | PowerPointテキスト抽出 |
| **python-dotenv** | 1.2.1 | 環境変数管理 |
| **shortuuid** | 1.0.13 | チャットID生成 |

---

# 🚀 環境構築と実行

## 📋 前提条件

- **Python 3.12**
- **OpenAI API Key**
- **Firebase認証ファイル** (`firebase-key.json`)

---

## 環境構築の2つの方法

本アプリケーションは以下2つの方法で実行できます。

1. **ローカル環境** - 自分のPC上に直接環境を構築
2. **Docker** - コンテナ環境で実行

---

## 1. ローカル環境で実行する場合

### ① リポジトリをクローン

```bash
git clone https://github.com/00-167cm/RAG-chatbot.git
cd RAG-chatbot
```

### ② 仮想環境を作成・有効化

```bash
python -m venv venv
source venv/bin/activate
```

### ③ パッケージをインストール

```bash
pip install -r requirements.txt
```

### ④ システム依存ツールのインストール

OCR機能に必要なツールをインストールしてください。

**macOS:**

```bash
brew install tesseract tesseract-lang poppler
```

**Windows:**

1. [Tesseract インストーラー](https://github.com/UB-Mannheim/tesseract/wiki) からインストール（インストール時に「Japanese」言語データを選択）
2. [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) をダウンロードし、展開先の `bin/` フォルダを環境変数 `PATH` に追加

### ⑤ 環境変数・認証ファイルの設定

プロジェクトルートに `.env` ファイルを作成し、以下を記述：

```
OPENAI_API_KEY="sk-..."
```

次に、Firebase認証ファイルを配置します：

1. [Firebase Console](https://console.firebase.google.com/) にアクセス
2. 対象プロジェクトを選択 →「プロジェクトの設定」→「サービスアカウント」
3. 「新しい秘密鍵の生成」をクリックし、JSONファイルをダウンロード
4. ダウンロードしたファイルを `firebase-key.json` にリネームし、`secrets/` ディレクトリに配置

### ⑥ 資料データの配置

RAG検索対象の資料を配置します。資料の取り込み元はGoogle Driveまたはローカルフォルダのどちらかを選択でき、`config/settings.py`の`DOC_SOURCE`で切り替えます。

対応ファイル形式は以下の通りです。

**通常ファイル**

- PDF (.pdf)
- HTML (.html)
- Excel (.xlsx / .xlsm)
- Word (.docx)
- PowerPoint (.pptx)

**Google Driveネイティブ形式（自動変換）**
Google Driveネイティブ形式のファイルは、`export_media()`でOffice形式に自動変換した後、上記の通常ファイルと同じパイプラインで処理されます。

- Googleスプレッドシート → .xlsx
- Googleドキュメント → .docx
- Googleスライド → .pptx

**ローカルから取り込む場合（`DOC_SOURCE = "local"`）：**

`data/documents/` ディレクトリに対応形式のファイルを配置してください。

```
data/
  └── documents/
       ├── 審査手順(顧客属性別).pdf
       ├── 審査手順(収入証明書).pdf
       ├── 審査手順(本人確認書類).pdf
       ├── 業務マニュアル.docx          ← Word も対応
       └── 集計データ.xlsx              ← Excel も対応
```

**Google Driveから取り込む場合（`DOC_SOURCE = "gd"`）：**

`.env` に `GD_FOLDER_ID` を追加し、`secrets/gc_service_account.json` にサービスアカウントキーを配置してください。起動時にGoogle Driveから自動で資料を取得・ベクトル化します。

```
GD_FOLDER_ID="your-folder-id"
```

> 💡 お手元に資料がない場合は、デモ用資料をご利用いただけます：[📁 Google Drive 資料格納先](https://drive.google.com/drive/folders/1STi-Pg3OBtFP1-9pZvw4FTOIWu2m_zch?usp=sharing)
> 

### ⑦ アプリを起動

```bash
python -m streamlit run main.py
```

ブラウザで `http://localhost:8501` にアクセスしてください。

## 2. Dockerで実行する場合

### ① リポジトリをクローン

```bash
git clone https://github.com/00-167cm/RAG-chatbot.git
cd RAG-chatbot
```

### ② 環境変数を設定

プロジェクトルートに `.env` ファイルを作成し、以下を記述：

```
OPENAI_API_KEY=sk-...
```

Firebase認証ファイル `firebase-key.json` を `secrets/` ディレクトリに配置してください。

### ③ Dockerイメージをビルド

```bash
docker build -t rag-chatbot .
```

Dockerfile内でTesseract OCR・Poppler等のシステム依存ツールも自動的にインストールされます。

### ④ コンテナを起動

```bash
docker run -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/secrets/firebase-key.json:/secrets/firebase-key.json \
  rag-chatbot
```

ブラウザで `http://localhost:8080` にアクセスしてください。

---

### ベクトルDBについて（ローカル環境）

ベクトルDBはローカル環境では `data/chroma_db/` に永続化されるため、一度ベクトル化すればアプリを再起動してもデータは保持されます。

**自動でベクトル化されるタイミング：**

アプリ起動時にベクトルDBが空の場合、`DOC_SOURCE` の設定に応じてローカルまたはGoogle Driveから資料を自動取り込みします。

> 💡 デモ環境（Cloud Run）ではコンテナが一定時間アクセスされないと自動停止し、次回アクセス時に新しいコンテナが起動します。その際ベクトルDBは空の状態から再構築されます。
> 

**資料を入れ替えたい場合：**

`data/documents/` 内のファイルを差し替えた後、以下を実行してください：

```bash
rm -rf data/chroma_db
mkdir data/chroma_db
python -m streamlit run main.py
```

既存のベクトルDBを削除してからアプリを起動することで、新しい資料で再ベクトル化されます。

## コマンド一覧

**ローカル環境**

```bash
git clone https://github.com/00-167cm/RAG-chatbot.git
cd RAG-chatbot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
brew install tesseract tesseract-lang poppler  # macOS
# .envファイルをプロジェクトルートに配置
# firebase-key.jsonをsecrets/に配置
# 対応形式のファイルをdata/documents/に配置
python -m streamlit run main.py
```

**Docker**

```bash
git clone https://github.com/00-167cm/RAG-chatbot.git
cd RAG-chatbot
# .envファイルをプロジェクトルートに配置
# firebase-key.jsonをsecrets/に配置
docker build -t rag-chatbot .
docker run -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/secrets/firebase-key.json:/secrets/firebase-key.json \
  rag-chatbot
```
