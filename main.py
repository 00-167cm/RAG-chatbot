import streamlit as st
from chat.gui import GUI
from chat.chat_manager import ChatManager
from chat.langchain_manager import LangChainManager
from infrastructure.db_manager import DBManager
from infrastructure.rag_manager import RAGManager
from config.settings import (
    RAG_THRESHOLD, WINDOW_TITLE, COLLECTION_NAME,
    DOC_SOURCE, GD_FOLDER_ID, CHROMA_DB_PATH
)

# ページ設定
st.set_page_config(page_title=WINDOW_TITLE, layout="wide")


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
        documents_path="data/documents",
        chroma_path="data/chroma_db",
        collection_name=COLLECTION_NAME,
        threshold=RAG_THRESHOLD
    )
    
    # ========================================
    # ベクトルDBにデータがなければ自動取り込み
    # ========================================
    collection_info = rag_manager.chroma_manager.get_collection_info()
    
    if collection_info["chunk_count"] == 0:
        print(f"📂 ベクトルDBが空です。DOC_SOURCE='{DOC_SOURCE}' で取り込みを開始します...")
        
        if DOC_SOURCE == "local":
            # ローカルフォルダから取り込み
            print("📁 ローカルフォルダから資料を取り込み中...")
            rag_manager.process_all_pdfs()
            
        elif DOC_SOURCE == "gd":
            # Google Driveから取り込み
            if not GD_FOLDER_ID:
                print("❌ GD_FOLDER_IDが設定されていません。.envを確認してください。")
            else:
                print(f"☁️ Google Driveから資料を取り込み中... (Folder ID: {GD_FOLDER_ID})")
                from infrastructure.google_drive_vectorizer import GoogleDriveVectorizer
                vectorizer = GoogleDriveVectorizer(
                    service_account_path="secrets/gc_service_account.json"
                )
                chunks = vectorizer.get_chunks(folder_id=GD_FOLDER_ID)
                if chunks:
                    rag_manager.chroma_manager.add_documents(chunks)
        else:
            print(f"⚠️ 不明なDOC_SOURCE: '{DOC_SOURCE}'。'local' または 'gd' を指定してください。")
    else:
        print(f"✅ ベクトルDBにデータあり（{collection_info['chunk_count']}チャンク）。取り込みスキップ。")
    
    return db_manager, langchain_manager, rag_manager


# キャッシュされたマネージャーを取得
db_manager, langchain_manager, rag_manager = get_cached_managers()

# ChatManagerの初期化（session_stateを使うのでキャッシュしない）
chat_manager = ChatManager(db_manager, langchain_manager, rag_manager)

# GUIの初期化
gui = GUI(chat_manager, langchain_manager, rag_manager)

# アプリケーション実行
if __name__ == "__main__":
    gui.run()
