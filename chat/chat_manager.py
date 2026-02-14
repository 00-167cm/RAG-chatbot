"""
🟡 ChatManager (処理の振り分けを行うコントローラー)GUI ⇄ DB ⇄ LangChain をつなぐ
    【役割】
    - 各チャットの会話履歴を管理
    - DBとGUIの橋渡し
    - データの加工(DB形式 ↔ session_state形式)
    - チャットの作成・削除・更新
    - タイトルの自動生成
    【重要】Streamlitは再実行されるたびにインスタンスが作り直されるため、
    session_stateから値を復元して「正」のデータを保持する
"""
import streamlit as st
import shortuuid
from typing import List, Dict, Any, Optional

class ChatManager:
    """
    チャット管理のコントローラークラス
    
    【このクラスが持つデータ】
    - self.db_manager: DBManagerのインスタンス(Firestore操作用)
    - self.langchain_manager: LangChainManagerのインスタンス(AI連携用)
    - self.rag_manager: RAGManagerのインスタンス(RAG操作用)
    - self.chat_list: チャット一覧 [{"id": "xxx", "title": "xxx"}, ...]
    - self.all_chat_histories: 全チャットの会話履歴（遅延読み込み）
        {"chat_id": [{"role": "user", "content": "..."}, ...]}
    """
    def __init__(self, db_manager, langchain_manager, rag_manager=None):
        """
        チャット管理のコントローラーを初期化する
        ChatManagerはGUI、DB、LangChainをつなぐ橋渡し役として、
        チャットの作成・削除・更新、会話履歴の管理、タイトルの自動生成を行う

        Args:
            db_manager: Firebase Firestoreとの接続を管理するDBManagerインスタンス
            langchain_manager: OpenAIとの連携を管理するLangChainManagerインスタンス
            rag_manager: 社内資料の検索を管理するRAGManagerインスタンス（オプショナル）
        """
        # 引数をインスタンス変数に保存
        self.db_manager = db_manager
        self.langchain_manager = langchain_manager
        self.rag_manager = rag_manager
        
        # session_stateから復元
        # この関数で self.chat_list と self.all_chat_histories が設定される
        self._restore_from_session_state()
    
    def _restore_from_session_state(self):
        """
        session_stateから値を復元、なければFirestoreから取得
        """
        # session_stateに"chat_list"がある = 既にデータが存在
        if "chat_list" in st.session_state:
            # 既存データがあれば復元（キャッシュ）
            self.chat_list = st.session_state.chat_list
            self.all_chat_histories = st.session_state.get("all_chat_histories", {})
        else:
            # Firestoreからチャット一覧のみ取得（履歴は取得しない！）
            self.chat_list = self._load_chat_list_from_db()
            self.all_chat_histories = {}  # 🆕 空辞書で初期化（遅延読み込み）
            
            # session_stateに保存(キャッシュ)
            st.session_state.chat_list = self.chat_list
            st.session_state.all_chat_histories = self.all_chat_histories
    
    def _load_chat_list_from_db(self) -> List[Dict[str, str]]:
        """
        Firestoreからチャット一覧を取得
        
        Returns:
            チャット一覧 [{"id": "xxx", "title": "xxx"}, ...]
        """
        return self.db_manager.get_all_chats()
    
    def get_chat_list(self) -> List[Dict[str, str]]:
        """
        チャット一覧を取得

        Returns:
        [{"id": "xxx", "title": "xxx"}, ...]
        """
        return self.chat_list
    
    def get_current_chat_id(self, chat_list: List[Dict[str, str]]) -> str:
        """
        デフォルトで選択するチャットIDを返す
        chat_listの最初の要素のIDを返す

        Returns:
            チャットID(文字列)
        """
        if chat_list:
            return chat_list[0]["id"]
        else:
            # チャットリストが空の場合は新規作成
            return shortuuid.uuid()
    
    def get_chat_title_by_id(self, chat_id: str) -> str:
        """
        チャットIDからタイトルを取得
        
        Args:
            chat_id: チャットID
        
        Returns:
            チャットタイトル(文字列)
        """
        for chat in self.chat_list:
            if chat["id"] == chat_id:
                # IDが一致したらタイトルを返す
                return chat["title"]
            
        return "不明なチャット"
    
    def get_chat_histories(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        指定したチャットIDの会話履歴を取得

        Args:
            chat_id: チャットID
        
        Returns:
            会話履歴のリスト
            [{"role": "user", "content": "...", "is_rag": False}, ...]
        
        保存先：
            取得後は self.all_chat_histories と st.session_state にキャッシュされる
        """
        # 🆕 キャッシュにあればそれを返す
        if chat_id in self.all_chat_histories:
            return self.all_chat_histories[chat_id]
        
        # 🆕 キャッシュになければFirestoreから取得
        histories = self.db_manager.get_chat_history(chat_id)
        
        # 🆕 キャッシュに保存
        self.all_chat_histories[chat_id] = histories
        st.session_state.all_chat_histories = self.all_chat_histories
        
        return histories
    
    def add_message(
        self,
        chat_id: str,
        role: str,
        content: str,
        is_rag: bool = False,
        chunks: List[Dict[str, Any]] = None
    ):
        """
        チャットにメッセージを追加して全ての場所に保存する
        
        Args:
            chat_id: メッセージを追加するチャットのID
            role: メッセージの役割 ("user" または "assistant")
            content: メッセージの内容
            is_rag: RAGモードで生成されたメッセージかどうか（assistantメッセージのみ）
            chunks: RAG使用時の参照チャンク情報（assistantメッセージのみ）
        
        保存先：
            1. ChatManagerのメモリキャッシュ (self.all_chat_histories)
            2. Streamlitのsession_state (st.session_state.all_chat_histories)
            3. Firebase Firestore
        """
        # メッセージ辞書を作成
        message = {
            "role": role,
            "content": content
        }

        # assistantメッセージの場合のみis_ragとchunksを追加
        if role == "assistant":
            message["is_rag"] = is_rag
            # RAGモードの場合はチャンク情報を追加
            if is_rag and chunks:
                message["chunks"] = chunks

        # ChatManager側のデータを更新
        # chat_idがall_chat_historiesに存在しない場合、空リストを作成
        if chat_id not in self.all_chat_histories:
            self.all_chat_histories[chat_id] = []

        # リストにメッセージを追加
        self.all_chat_histories[chat_id].append(message)

        # session_stateにも同期(これがないとStreamlit再実行時にデータが消える)
        st.session_state.all_chat_histories = self.all_chat_histories

        # Firestoreにも保存
        self.db_manager.save_message(
            chat_id=chat_id,
            role=role,
            content=content,
            is_rag=is_rag if role == "assistant" else None,
            chunks=chunks
        )
    
    def create_new_chat_with_title(self, title: str) -> Dict[str, str]:
        """
        新しいチャットを作成してIDとタイトルを返す
        
        Args:
            title: 新しいチャットのタイトル
        
        Returns:
            作成されたチャット情報 {"id": "xxx", "title": "xxx"}
        
        保存先：
            1. Firestoreに新しいチャットを作成
            2. chat_listに追加（先頭に）
            3. all_chat_historiesに空リストを作成
            4. session_stateに同期
        """
        # Firestoreに作成（自動IDを取得）
        new_id = self.db_manager.create_chat(title=title)
        
        if new_id is None:
            # 作成失敗時はローカルIDを生成
            new_id = shortuuid.uuid()
        
        new_chat = {"id": new_id, "title": title}
        
        # ChatManager側のデータを更新
        # リストの先頭に追加（新しいチャットが一番上に来るように）
        self.chat_list.insert(0, new_chat)
        self.all_chat_histories[new_id] = []
        
        # session_stateにも同期
        st.session_state.chat_list = self.chat_list
        st.session_state.all_chat_histories = self.all_chat_histories
        
        return new_chat
    
    def format_chat_histories(self, chat_histories: List[Dict[str, str]]) -> List[Any]:
        """
        会話履歴をLangChainに渡す用に整形
        
        【変換前(通常形式)】
        [
            {"role": "user", "content": "こんにちは"},
            {"role": "assistant", "content": "やあ!"}
        ]
        
        【変換後(LangChain形式)】
        [
            HumanMessage(content="こんにちは"),
            AIMessage(content="やあ!")
        ]
        
        Args:
            chat_histories: 通常形式の会話履歴
        
        Returns:
            LangChain形式のメッセージリスト
        """
        lc_chat_list = []
        for chat in chat_histories:
            if chat["role"] == "user":
                # langchain_managerを使ってHumanMessageを作成
                content = self.langchain_manager.create_human_message(chat["content"])
                lc_chat_list.append(content)
            elif chat["role"] == "assistant":
                # langchain_managerを使ってAIMessageを作成
                content = self.langchain_manager.create_ai_message(chat["content"])
                lc_chat_list.append(content)
        # 変換されたリストを返す
        return lc_chat_list
    
    def update_chat_title(self, chat_id: str, new_title: str):
        """
            チャットのタイトルを更新
            
        Args:
            chat_id: タイトルを更新するチャットのID
            new_title: 新しいタイトル
        
        保存先：
            1. chat_listの該当チャットのタイトルを更新
            2. session_stateに同期
            3. Firestoreに保存
        """
        for chat in self.chat_list:
            if chat["id"] == chat_id:
                chat["title"] = new_title
                break
        
        # session_stateにも同期
        st.session_state.chat_list = self.chat_list
        
        # Firestoreにも保存
        self.db_manager.update_chat_title(chat_id, new_title)
    
    def should_generate_title(self, chat_id: str) -> bool:
        """
        タイトルを自動生成すべきかどうかを判定

        Args:
            chat_id: 判定するチャットのID

        Returns:
            True: タイトル生成すべき / False: 不要
        """
        # 現在のタイトルを取得
        current_title = self.get_chat_title_by_id(chat_id)
        
        # 「新規チャット」で始まるかチェック
        if not current_title.startswith("新規チャット"):
            return False
        
        # メッセージ数をチェック
        histories = self.get_chat_histories(chat_id)
        # AI応答完了後 = 2件以上(ユーザー + AI)
        if len(histories) >= 2:
            return True
        
        return False
    
    def generate_chat_title(self, chat_id: str) -> str:
        """
        会話内容からタイトルを自動生成
        
        Args:
            chat_id: タイトルを生成するチャットのID
        
        Returns:
            生成されたタイトル
        """
        # 会話履歴を取得
        histories = self.get_chat_histories(chat_id)
        
        # 最初の2件のメッセージを取得(タイトル生成に使用)
        recent_messages = histories[:2]
        
        # LangChain形式に変換
        formatted_messages = self.format_chat_histories(recent_messages)
        
        # LangChainManagerにタイトル生成を依頼
        title = self.langchain_manager.generate_title(formatted_messages)
        
        return title
    
    # RAG関連メソッド
    def get_rag_manager(self):
        """
        RAGManagerを取得
        
        Returns:
            RAGManagerのインスタンス（なければNone）
        """
        return self.rag_manager
    
    def refresh_from_db(self):
        """
        Firestoreから最新データを再取得する
        
        キャッシュをクリアしてDBから読み直し、データの同期が必要な時に使用する。
        例：別のセッションで更新があった時、データの同期が必要な時
        
        保存先：
            1. Firestoreからチャット一覧を再取得
            2. all_chat_historiesをクリア（遅延読み込みで再取得）
            3. session_stateを更新
        """
        # Firestoreから再取得（チャット一覧のみ）
        self.chat_list = self._load_chat_list_from_db()
        self.all_chat_histories = {}
        
        
        # session_stateを更新
        st.session_state.chat_list = self.chat_list
        st.session_state.all_chat_histories = self.all_chat_histories
        
        print("✅ Firestoreから最新データを取得しました")