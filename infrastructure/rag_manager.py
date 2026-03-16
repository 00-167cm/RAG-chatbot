"""
🤖 RAG管理
    RAG（検索拡張生成）の全体制御を行う
    
【役割】
- DocumentProcessorとChromaManagerの統合
- PDFの自動処理パイプライン
- RAGモードと通常モードの判定
- RAG用プロンプトの生成
"""
import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from infrastructure.document_processor import DocumentProcessor
from infrastructure.chroma_manager import ChromaManager
from config.settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    RAG_THRESHOLD,
    TOP_K_RESULTS,
    COLLECTION_NAME
)

class RAGManager:
    """
    RAG管理クラス
    PDF処理からベクトル検索、回答生成まで一貫して管理
    
    【このクラスが持つデータ】
    - self.document_processor: PDF処理担当
    - self.chroma_manager: ベクトルDB担当
    - self.documents_path: PDFを置くディレクトリ
    - self.threshold: RAG使用判定の閾値
    """
    
    def __init__(
        self,
        documents_path: str = "data/documents",
        chroma_path: str = "data/chroma_db",
        collection_name: str = COLLECTION_NAME,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        threshold: float = RAG_THRESHOLD
    ):
        """
        RAGManager初期化

        Args:
            documents_path: PDFを格納するディレクトリ
            chroma_path: ChromaDBの永続化先
            collection_name: コレクション名
            chunk_size: チャンクサイズ
            chunk_overlap: チャンク重複サイズ
            threshold: RAG使用判定の閾値（距離がこれ以下ならRAG使用）
        """
        self.documents_path = documents_path
        self.threshold = threshold
        
        # ディレクトリ作成
        Path(documents_path).mkdir(parents=True, exist_ok=True)
        
        # DocumentProcessorを初期化
        self.document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # ChromaManagerを初期化
        self.chroma_manager = ChromaManager(
            persist_directory=chroma_path,
            collection_name=collection_name
        )
        
        print(f"✅ RAGManager初期化完了")
        print(f"   ドキュメント格納先: {documents_path}")
    
    def process_and_store_pdf(self, pdf_path: str) -> bool:
        """
        PDFを処理してChromaDBに格納（単一ファイル）

        Args:
            pdf_path: PDFファイルのパス
        
        Returns:
            成功した場合True
        """
        print(f"\n📄 PDF処理開始: {pdf_path}")
        
        # チャンクに分割
        chunks = self.document_processor.process_pdf(pdf_path)
        
        if not chunks:
            return False
        
        # ChromaDBに格納
        result = self.chroma_manager.add_documents(chunks)
        
        return result
    
    def process_all_pdfs(self) -> bool:
        """
        ドキュメントディレクトリ内の全PDFを処理
        
        Returns:
            成功した場合True
        """
        print(f"\n📁 ディレクトリ処理開始: {self.documents_path}")
        
        # 全PDFをチャンク化
        all_chunks = self.document_processor.process_directory(self.documents_path)
        
        if not all_chunks:
            return False
        
        # ChromaDBに格納
        result = self.chroma_manager.add_documents(all_chunks)
        
        return result
    
    def query(
        self,
        user_question: str,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        ユーザーの質問に対してRAG検索を実行
        
        Args:
            user_question: ユーザーの質問        
        Returns:
            (関連ドキュメントリスト, RAGを使うべきか)
        """
        return self.chroma_manager.search_with_threshold(
            query=user_question,
            threshold=self.threshold,
            n_results=TOP_K_RESULTS
        )
    
    def build_rag_context(
        self,
        search_results: List[Dict[str, Any]]
    ) -> str:
        """
        検索結果をAIが読みやすい形にまとめる
        
        フォーマット：
            【参照資料1】(ファイル名 / ページ番号)
            テキスト内容...
            
            【参照資料2】(ファイル名 / ページ番号)
            テキスト内容...
        """
        if not search_results:
            return ""
        
        context_parts = []
        
        for i, result in enumerate(search_results, start=1):
            source = result["metadata"].get("source", "不明")
            page = result["metadata"].get("page", "?")
            text = result["text"]
            
            context_parts.append(
                f"【参照資料{i}】({source} / ページ{page})\n{text}"
            )
        
        return "\n\n".join(context_parts)
    
    def build_rag_prompt(
            self,
            user_question: str,
            context: str
        ) -> str:
            """
            AIに送るための質問文を作成する（RAG用）
            
            Args:
                user_question: ユーザーの質問
                context: 検索結果から構築した参照資料テキスト
            
            Returns:
                RAG用プロンプト（参照資料 + 質問）
            
            Note:
                AIの振る舞いルールはsettings.pyのSYSTEM_PROMPT_RAGで定義
            """
            return f"""===== 参照資料 =====
    {context}
    ====================

    ユーザーの質問: {user_question}"""
    
    def get_rag_response_data(
        self,
        user_question: str
    ) -> Dict[str, Any]:
        """
        ユーザーの質問に対してRAG検索を実行する
        
        Args:
            user_question: ユーザーの質問
        
        Returns:
            • use_rag: RAGを使うかどうか
            • context: 関連資料のテキスト
            • prompt: AIに渡すプロンプト
            • search_results: 検索結果
        """
        # 検索実行
        results, use_rag = self.query(user_question)

        if not use_rag:
            return {
                "use_rag": False,
                "context": "",
                "prompt": "",
                "search_results": []
            }
        
        # コンテキスト構築
        context = self.build_rag_context(results)
        
        # プロンプト構築
        prompt = self.build_rag_prompt(user_question, context)
        
        return {
            "use_rag": True,
            "context": context,
            "prompt": prompt,
            "search_results": results
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        RAGシステムの状態を取得
        
        Returns:
            {
                "documents_path": "data/documents",
                "collection_info": {...},
                "threshold": 0.1
            }
        """
        return {
            "documents_path": self.documents_path,
            "collection_info": self.chroma_manager.get_collection_info(),
            "threshold": self.threshold
        }
    
    def get_google_drive_link(self, filename: str, metadata: dict = None) -> str:
        """
        メタデータからGoogleドライブのURLを返す
        メタデータにdrive_urlがない場合（ローカルモード）は空文字を返す
        """
        if metadata and metadata.get("drive_url"):
            return metadata["drive_url"]
        return ""
    
    def reload_documents(self) -> bool:
        """ドキュメントを再読み込み"""
        print("\n🔄 ドキュメント再読み込み開始...")
        self.chroma_manager.clear_collection()
        return self.process_all_pdfs()
