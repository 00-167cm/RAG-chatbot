"""
チャットボットシステム - 共通設定ファイル
プロジェクト全体で使用する定数・設定値を一元管理

【このファイルの役割】
- 全プロジェクトで統一された設定値を管理

【使用例】
from config.settings import JST, OPENAI_MODEL
"""

import os
from datetime import timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# ========================================
# プロジェクトルートパスの設定
# ========================================
# このファイルの位置から2階層上がプロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# ========================================
# タイムゾーン設定
# ========================================
# 日本標準時 (UTC+9)
# さくら金融の業務記録は全てJSTで統一
JST = timezone(timedelta(hours=9))

# ========================================
# OpenAI API設定
# ========================================
OPENAI_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LangChain設定
TEMPERATURE = 0.1
# AIの応答の多様性 (0.0-1.0)
# 0.0: 毎回同じような応答（一貫性重視）
# 1.0: 毎回違う応答（創造性重視）
# 0.7: バランスが良い（推奨）

# ========================================
# ChromaDB設定
# ========================================
CHROMA_DB_PATH = PROJECT_ROOT / "data" / "chroma_db"
# TODO acomっていう固有名詞を変える
COLLECTION_NAME = "acom_documents"

# ========================================
# ドキュメント設定
# ========================================
DOCUMENTS_PATH = PROJECT_ROOT / "data" / "documents"

# チャンク設定 (RAG用のテキスト分割設定)
CHUNK_SIZE = 500  # 1チャンクの文字数
CHUNK_OVERLAP = 100  # チャンク間のオーバーラップ文字数

# ========================================
# RAG設定
# ========================================
# RAG使用判定の閾値（類似度スコア）
RAG_THRESHOLD = 1.2
# 閾値の考え方:
# - スコアが低いほど関連性が高い
# - 0.0-1.0: 非常に関連性が高い（RAG推奨）
# - 1.0-1.5: 関連性あり（RAG使用可）
# - 1.5以上: 関連性が低い（通常回答推奨）
MIN_VALUE = 0.0
MAX_VALUE = 2.0
STEP = 0.1

# 類似度検索で取得する関連文書数
TOP_K_RESULTS = 3

# ========================================
# Streamlit GUI設定
# ========================================
WINDOW_TITLE = "AIチャット"

# ========================================
# タイトル生成設定
# ========================================
# チャットタイトルの最大文字数
TITLE_MAX_LENGTH = 15

# ===================
# Google Drive
# ===================
GOOGLE_DRIVE_FOLDER_URL = os.getenv("GOOGLE_DRIVE_FOLDER_URL")
# ========================================
# Firebase設定
# ========================================
if os.path.exists("/secrets/firebase-key.json"):
    FIREBASE_CREDENTIAL_PATH = "/secrets/firebase-key.json"
else:
    FIREBASE_CREDENTIAL_PATH = "firebase-key.json"

# ========================================
# プロンプト設定
# ========================================

# 通常モードのシステムプロンプト
SYSTEM_PROMPT_NORMAL = """あなたはフレンドリーで親切なAIアシスタントです。ユーザーの質問に対して、明るくわかりやすく丁寧に答えてください。"""

# RAGモードのシステムプロンプト
# TODO 資料の中身綺麗にする（例：NSC業務フローなど固有名詞排除）
SYSTEM_PROMPT_RAG = """あなたは会社での業務サポートAIです。

【重要なルール】
1. 回答の冒頭に「NSC業務フローに基づき」または「横浜センターのローカルルールによると」という接頭語を付けてください
2. 参照資料に書かれている情報のみを使用してください
3. 具体的なコード名やルール名（NSCコード、NG理由コード表など）がある場合は、それを明記してください
4. 分かりやすく、丁寧に回答してください

参照資料がある場合は、それに基づいて回答します。"""

# タイトル生成用プロンプト
SYSTEM_PROMPT_TITLE = """以下の会話内容を要約して、15文字以内の短いタイトルを生成してください。

ルール:
- 15文字以内で簡潔に
- 会話の主要なテーマを捉える
- 「〜について」などの余計な言葉は省く
- タイトルのみを出力(説明文は不要)

例:
会話: Pythonの基本文法について教えて → タイトル: Python文法
会話: おすすめのカフェを教えて → タイトル: おすすめカフェ
会話: ストレス解消法について → タイトル: ストレス解消"""

# ========================================
# Googleドライブ設定
# ========================================
# ファイル別のGoogleドライブリンク
# TODO 
GOOGLE_DRIVE_LINKS = {
    "顧客属性別審査ルール集.pdf": "https://drive.google.com/file/d/14AaFxoYSNWDMM3nOUffnC8qMN6A-KOhW/view?usp=sharing",
    "収入証明書確認ルール集.pdf": "https://drive.google.com/file/d/1f8G8_M2iiY1xLmAFx790EXjTHt4yVGtU/view?usp=sharing",
    "本人確認書類確認・登録ルール集.pdf": "https://drive.google.com/file/d/1FvZYlvjidbjZP57fSVLso6ufuCJXKoNH/view?usp=sharing"
}