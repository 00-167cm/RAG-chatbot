"""
🗄️ Chroma管理
    ChromaDBへのベクトル格納と検索を行う
    
【役割】
- ChromaDBへの接続（永続化対応）
- ドキュメントのベクトル化と格納
- 類似度検索
- コレクション管理
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from config.settings import EMBEDDING_MODEL,RAG_THRESHOLD,TOP_K_RESULTS, COLLECTION_NAME

class ChromaManager:
    """
    ChromaDB管理クラス
    ベクトルの格納と検索を担当
    
    【このクラスが持つデータ】
    - self.persist_directory: データ永続化先のパス
    - self.collection_name: コレクション名（テーブルのようなもの）
    - self.client: ChromaDBクライアント
    - self.collection: 使用中のコレクション
    - self.embeddings: OpenAI Embeddingsモデル
    """
    
    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = COLLECTION_NAME
    ):
        """
        ChromaManager初期化
        
        Args:
            persist_directory: データ保存先ディレクトリ
            collection_name: コレクション名
        
        【永続化とは】
        PCを再起動してもデータが消えないように
        ファイルとして保存すること
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "RAG検索用ドキュメントコレクション"}

        )
        
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL
        )
        
        print(f"✅ ChromaDB初期化完了")
        print(f"   永続化先: {persist_directory}")
        print(f"   コレクション: {collection_name}")
        print(f"   既存ドキュメント数: {self.collection.count()}")
    
    def add_documents(
        self,
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """
        ドキュメント（チャンク）をベクトル化して格納
        
        Args:
            chunks: DocumentProcessorで生成したチャンクリスト
                [{"text": "...", "metadata": {...}}, ...]
        
        Returns:
            成功した場合True
        """
        if not chunks:
            print("⚠️ 追加するチャンクがありません")
            return False
        
        try:
            texts = [chunk["text"] for chunk in chunks]
            
            metadatas = [chunk["metadata"] for chunk in chunks]
            
            ids = [
                f"{chunk['metadata']['source']}_{chunk['metadata']['page']}_{chunk['metadata']['chunk_index']}"
                for chunk in chunks
            ]
            
            print(f"🔄 ベクトル化中... ({len(texts)}件)")
            embeddings = self.embeddings.embed_documents(texts)
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"✅ {len(chunks)}件のチャンクを追加しました")
            print(f"   合計ドキュメント数: {self.collection.count()}")
            return True
            
        except Exception as e:
            print(f"❌ ドキュメント追加エラー: {e}")
            return False
    
    def search(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        類似度検索を実行
        
        Args:
            query: 検索クエリ（ユーザーの質問）
            n_results: 返す結果の数（デフォルト3件）
        
        Returns:
            検索結果のリスト
            [
                {
                    "text": "関連するテキスト...",
                    "metadata": {...},
                    "distance": 0.123
                },
                ...
            ]
        """
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted_results = []
            
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 検索エラー: {e}")
            return []
    
    def search_with_threshold(
        self,
        query: str,
        threshold: float = RAG_THRESHOLD,
        n_results: int = TOP_K_RESULTS
    ) -> tuple[List[Dict[str, Any]], bool]:
        """
        閾値付き類似度検索
        RAGモードで回答すべきか判定するために使用
        """
        results = self.search(query, n_results)
        
        if not results:
            return [], False
        
        best_distance = results[0]["distance"]

        print("best_distance: 👇ここが閾値を突破した資料")
        print(f"上位３件の数値:First:{results[0]["distance"]}:::::Second:{results[1]["distance"]}:::::third:{results[2]["distance"]}")
        print(f"best_distance: {best_distance}, threshold: {threshold}")
        print(results[0])
        print(" ============== end best distance =================")

        if best_distance <= threshold:
            return results, True
        
        else:
            return [], False
    
    def get_unique_sources_count(self) -> int:
        """
        格納されているユニークなソース（ファイル）の数を取得

        Returns:
            ユニークなファイル数
        """
        try:
            if self.collection.count() == 0:
                return 0
            
            results = self.collection.get(
                include=["metadatas"]
            )
            
            sources = set()
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    source = metadata.get("source")
                    if source:
                        sources.add(source)
            
            return len(sources)
            
        except Exception as e:
            print(f"❌ ソース数取得エラー: {e}")
            return 0
    
    def get_source_list(self) -> List[str]:
        """
        格納されているファイル名のリストを取得

        Returns:
            ファイル名のリスト
            例: ["業務フロー.html", "記録ルール.html", "rules.pdf"]
        """
        try:
            if self.collection.count() == 0:
                return []
            
            results = self.collection.get(include=["metadatas"])
            
            sources = set()
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    source = metadata.get("source")
                    if source:
                        sources.add(source)
            
            return sorted(list(sources))
            
        except Exception as e:
            print(f"❌ ソースリスト取得エラー: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        コレクションの情報を取得
        
        Returns:
            コレクション情報
            {
                "name": "rag_documents",
                "chunk_count": 18,
                "file_count": 3,
                "persist_directory": "data/chroma_db"
            }
        """
        return {
            "name": self.collection_name,
            "chunk_count": self.collection.count(),
            "file_count": self.get_unique_sources_count(),
            "persist_directory": self.persist_directory
        }
    
    def clear_collection(self) -> bool:
        """
        コレクション内の全データを削除
        （テスト時やリセット時に使用）
        
        Returns:
            成功した場合True
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG検索用ドキュメントコレクション"}

            )
            print(f"✅ コレクション '{self.collection_name}' をクリアしました")
            return True
            
        except Exception as e:
            print(f"❌ クリアエラー: {e}")
            return False
    
    def delete_by_source(self, source_name: str) -> bool:
        """
        特定のソース（ファイル）のドキュメントを削除
        
        Args:
            source_name: 削除するファイル名（例: "rules.pdf"）
        
        Returns:
            成功した場合True
        
        【使用例】
        chroma.delete_by_source("old_rules.pdf")
        chroma.add_documents(new_chunks)
        """
        try:
            self.collection.delete(
                where={"source": source_name}
            )
            print(f"✅ '{source_name}' のドキュメントを削除しました")
            return True
            
        except Exception as e:
            print(f"❌ 削除エラー: {e}")
            return False