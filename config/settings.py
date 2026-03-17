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
JST = timezone(timedelta(hours=9))

# ========================================
# OpenAI API設定
# ========================================
OPENAI_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LangChain設定
TEMPERATURE = 0.1

# ========================================
# ChromaDB設定
# ========================================
CHROMA_DB_PATH = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "rag_documents"

# ========================================
# 資料取り込み設定
# ========================================
# 取り込み方法の切り替え
# "local" → ローカルフォルダから取り込み
# "gd"    → Google Driveから取り込み
DOC_SOURCE = "gd"

# ローカル取り込み時のパス
LOCAL_DOC_PATH = PROJECT_ROOT / "data" / "documents"

# Google Drive取り込み時のフォルダID
GD_FOLDER_ID = os.getenv("GD_FOLDER_ID")

# チャンク設定（RAG用テキスト分割）
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# ========================================
# RAG設定
# ========================================
# RAG使用判定の閾値（類似度スコア）
RAG_THRESHOLD = 1.2
MIN_VALUE = 0.0
MAX_VALUE = 2.0
STEP = 0.1

# 類似度検索で取得する関連文書数
TOP_K_RESULTS = 3

# ========================================
# Streamlit GUI設定
# ========================================
WINDOW_TITLE = "RAGチャットボット"
MAIN_TITLE = "RAGチャットボット"
SIDEBAR_TITLE = "💬 チャット履歴"
RAG_SETTINGS_TITLE = "📚 RAG設定"
NEW_CHAT_TITLE = "新規チャット"

# ========================================
# タイトル生成設定
# ========================================
TITLE_MAX_LENGTH = 15

# ========================================
# Firebase設定
# ========================================
if os.path.exists("/secrets/firebase-key.json"):
    FIREBASE_CREDENTIAL_PATH = "/secrets/firebase-key.json"
else:
    FIREBASE_CREDENTIAL_PATH = "secrets/firebase-key.json"

# ========================================
# プロンプト設定
# ========================================

# 通常モードのシステムプロンプト
SYSTEM_PROMPT_NORMAL = """あなたはフレンドリーで親切なAIアシスタントです。ユーザーの質問に対して、明るくわかりやすく丁寧に答えてください。"""

# RAGモードのシステムプロンプト
SYSTEM_PROMPT_RAG = """あなたは、取り込まれた資料に基づいて質問に回答するAIアシスタントです。

【回答ルール】
1. 回答は必ず参照資料の内容に基づいてください
2. 資料に記載がない内容については「該当する情報は資料内に見つかりませんでした」と伝えてください
3. 資料内に専門用語やコード名がある場合は、そのまま正確に引用してください
4. わかりやすく丁寧に回答してください
5. 資料に書かれていない内容を推測で補わないでください"""

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
