"""
infrastructure/google_drive_vectorizer.py
Google Drive上のファイルを直接メモリ上で処理し、ChromaDBへベクトル化するクラス
"""
import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

# Google & LangChain Imports
from langchain_google_community import GoogleDriveLoader
from langchain_community.document_loaders import UnstructuredFileIOLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# 既存の設定ファイルを読み込み
from config.settings import (
    CHROMA_DB_PATH, 
    COLLECTION_NAME, 
    CHUNK_SIZE, 
    CHUNK_OVERLAP,
    EMBEDDING_MODEL
)

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleDriveVectorizer:
    """
    Google Drive → ChromaDB ベクトル化エンジン
    """
    
    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "google_token.json",
        persist_directory: str = CHROMA_DB_PATH,
        collection_name: str = COLLECTION_NAME
    ):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Embeddingsモデルの初期化
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        
        # Text Splitterの初期化 (日本語に強い区切り文字設定)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "、", " ", ""]
        )

    def _create_extension_filter(self):
        """拡張子によるフィルタリング関数を生成"""
        # 許可する拡張子
        ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv", ".html"}
        
        def extension_filter(search: Dict[str, Any], file: Dict[str, Any]) -> bool:
            mime_type = file.get("mimeType", "")
            file_name = file.get("name", "")
            
            # Google Docsなどは通す
            if mime_type.startswith("application/vnd.google-apps"):
                return True
            
            # 拡張子チェック
            ext = Path(file_name).suffix.lower()
            return ext in ALLOWED_EXTENSIONS
            
        return extension_filter

    def process_folder(
        self,
        folder_id: str,
        recursive: bool = True
    ) -> bool:
        """
        指定フォルダ内の全ファイルを処理してChromaDBに格納
        """
        if not self.credentials_path.exists():
            logger.error(f"❌ 認証ファイルが見つかりません: {self.credentials_path}")
            return False

        logger.info(f"📂 Google Driveフォルダ読み込み開始 (ID: {folder_id})")
        
        try:
            # 1. Google Drive Loaderの設定
            # UnstructuredFileIOLoaderを使うことで、PDFなどのバイナリもメモリ上で処理可能
            loader = GoogleDriveLoader(
                folder_id=folder_id,
                credentials_path=str(self.credentials_path),
                token_path=str(self.token_path),
                recursive=recursive,
                file_types=["document", "sheet", "slide", "pdf"], # Google形式 + PDF
                file_loader_cls=UnstructuredFileIOLoader, # バイナリ処理用ローダー
                file_loader_kwargs={"mode": "elements"},
                filter=self._create_extension_filter() # 拡張子フィルタ適用
            )

            # 2. ドキュメント読み込み
            documents = loader.load()
            if not documents:
                logger.warning("⚠️ 読み込めるドキュメントがありませんでした。")
                return False
                
            logger.info(f"📄 {len(documents)} 件のファイルを読み込みました。チャンク分割を開始します...")

            # 3. チャンク分割
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"🧩 {len(chunks)} 個のチャンクを作成しました。")

            # 4. メタデータの調整（ソースパスなどをきれいに）
            for doc in chunks:
                # ソース元がわかるようにメタデータを整理
                if 'source' in doc.metadata:
                    doc.metadata['source'] = Path(doc.metadata['source']).name

            # 5. ChromaDBへ保存（既存のコレクションがあれば追記、なければ作成）
            # langchain_chroma.Chroma を使用して保存
            Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory,
                collection_name=self.collection_name
            )
            
            logger.info(f"✅ ベクトル化完了！保存先: {self.persist_directory}")
            return True

        except Exception as e:
            logger.error(f"❌ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False

    def clear_collection(self):
        """コレクションの全削除（リセット用）"""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=self.persist_directory)
            client.delete_collection(self.collection_name)
            logger.info("🗑️ 既存のコレクションを削除しました。")
        except Exception as e:
            # コレクションがない場合は無視
            logger.info("ℹ️ 新規作成として処理します。")