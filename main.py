"""
エントリーポイント(全体起動スイッチ)
アプリケーションの起動と初期化を行う

【役割】
- 環境変数の読み込み
- ページ設定
- 各マネージャーのインスタンス化
- アプリケーションの実行

【🆕 最適化ポイント】
- @st.cache_resourceでRAGManager/ChromaManagerをキャッシュ
- Streamlit再実行時に毎回初期化されるのを防ぐ
"""
import streamlit as st
from chat.gui import GUI
from chat.chat_manager import ChatManager
from chat.langchain_manager import LangChainManager
from infrastructure.db_manager import DBManager
from infrastructure.rag_manager import RAGManager
from config.settings import RAG_THRESHOLD

# ページ設定
st.set_page_config(page_title="さくらのAIチャットボット", layout="wide")


@st.cache_resource
def get_cached_managers():
    """
    重い初期化処理をキャッシュする
    
    【キャッシュされるもの】
    • DBManager (Firebase接続)
    • LangChainManager (OpenAI接続) 
    • RAGManager (ChromaDB接続)
    
    Returns:
        (db_manager, langchain_manager, rag_manager) - 初期化済みマネージャー
    """
    # DBManager初期化（Firebase接続）
    db_manager = DBManager()
    
    # LangChainManager初期化（OpenAI接続）
    langchain_manager = LangChainManager()
    
    # RAGManager初期化（ChromaDB接続 + OpenAI Embeddings）
    rag_manager = RAGManager(
        # 【PDF保存場所】審査ルールPDFが入っているフォルダ
        documents_path="data/documents",
        # 【ベクトルDB保存場所】検索用データベースの保存先
        chroma_path="data/chroma_db",
        # 【コレクション名】ChromaDB内のテーブル名
        collection_name="acom_documents",
        threshold=RAG_THRESHOLD
    )
    
    return db_manager, langchain_manager, rag_manager


# 🆕 キャッシュされたマネージャーを取得
db_manager, langchain_manager, rag_manager = get_cached_managers()

# ChatManagerの初期化（これはsession_stateを使うのでキャッシュしない）
chat_manager = ChatManager(db_manager, langchain_manager, rag_manager)

# GUIの初期化（RAGManagerを渡す）
gui = GUI(chat_manager, langchain_manager, rag_manager)

# アプリケーション実行
if __name__ == "__main__":
    gui.run()