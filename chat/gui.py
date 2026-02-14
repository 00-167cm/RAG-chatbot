"""
GUI管理（画面表示と操作の担当）

役割：
    • チャット画面の表示
    • ユーザー入力の受け取り
    • ChatManagerへの指示出し
    • AI応答の表示
    • RAGモードの判定と表示

設計思想：
    データはChatManagerが「正」。GUIは表示だけ担当
    GUI → ChatManager → session_state の順で更新
"""
import streamlit as st
from typing import Dict, List, Any, Optional
import shortuuid

from config.settings import GOOGLE_DRIVE_FOLDER_URL, MIN_VALUE, MAX_VALUE, STEP
from infrastructure.rag_manager import RAGManager
from chat.chat_manager import ChatManager
from chat.langchain_manager import LangChainManager


class GUI:
    """
    GUI管理クラス
    
    データの流れ：
        ChatManager(正のデータ) → session_state → 画面表示
        ユーザー入力 → GUI → ChatManager → session_state → Firestore
    """
    
    def __init__(
        self, 
        chat_manager: ChatManager, 
        langchain_manager: LangChainManager, 
        rag_manager: Optional[RAGManager] = None
    ):
        """
        Args:
            chat_manager: 会話を管理するChatManagerインスタンス
            langchain_manager: AIと会話するLangChainManagerインスタンス
            rag_manager: 資料を検索するRAGManagerインスタンス（オプショナル）
        """
        self.chat_manager = chat_manager
        self.langchain_manager = langchain_manager
        self.rag_manager = rag_manager
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Streamlitのセッション状態を初期化"""
        if "current_chat" not in st.session_state:
            st.session_state.current_chat = {}
                
        if "id" not in st.session_state.current_chat:
            st.session_state.current_chat["id"] = self.chat_manager.get_current_chat_id(
                self.chat_manager.chat_list
            )
        
        if "title" not in st.session_state.current_chat:
            current_id = st.session_state.current_chat["id"]
            st.session_state.current_chat["title"] = self.chat_manager.get_chat_title_by_id(current_id)
    
    def _update_current_chat(self, new_id: str):
        """選択中のチャットIDを更新"""
        st.session_state.current_chat["id"] = new_id
        st.session_state.current_chat["title"] = self.chat_manager.get_chat_title_by_id(new_id)
    
    def _add_user_message(self, user_input: str):
        """
        ユーザーのメッセージを全ての保存先に追加
        
        保存先：
            1. ChatManagerのall_chat_histories
            2. st.session_state.all_chat_histories
            3. Firebase Firestore
        """
        current_id = st.session_state.current_chat["id"]
        chat_histories = self.chat_manager.get_chat_histories(current_id)
        
        # 履歴が空 = 最初のメッセージ → Firestoreにチャットを作成
        if len(chat_histories) == 0:
            current_title = st.session_state.current_chat["title"]
            self.chat_manager.db_manager.create_chat(
                chat_id=current_id,
                title=current_title
            )        

        self.chat_manager.add_message(current_id, "user", user_input)
    
    def _add_ai_message(
        self, 
        ai_response: str, 
        is_rag: bool = False,
        chunks: List[Dict[str, Any]] = None
    ):
        """AIメッセージを追加（ChatManager経由でFirestoreにも保存）"""
        self.chat_manager.add_message(
            st.session_state.current_chat["id"],
            "assistant",
            ai_response,
            is_rag=is_rag,
            chunks=chunks
        )
    
    def _auto_generate_title_if_needed(self) -> bool:
        """必要に応じてタイトルを自動生成。生成した場合Trueを返す"""
        current_id = st.session_state.current_chat["id"]
        
        if not self.chat_manager.should_generate_title(current_id):
            return False
        
        try:
            new_title = self.chat_manager.generate_chat_title(current_id)
            self.chat_manager.update_chat_title(current_id, new_title)
            st.session_state.current_chat["title"] = new_title
            return True
        except Exception as e:
            print(f"タイトル生成エラー: {e}")
            return False
    
    def _render_title(self): 
        st.title("RAGチャットボット")
    
    def _render_sidebar(self):
        """サイドバー（チャット履歴・RAG設定）を表示"""
        st.sidebar.title("💬 チャット履歴")
        
        chat_list = self.chat_manager.chat_list
        
        # 空のチャットがあるかチェック
        has_empty_chat = any(
            len(self.chat_manager.get_chat_histories(chat["id"])) == 0
            for chat in chat_list
        )
        
        # 新規チャット作成ボタン
        if st.sidebar.button(
            "➕ 新規チャット", 
            key="new_chat_button", 
            use_container_width=True,
            disabled=has_empty_chat,
            help="💬 空のチャットがあります。メッセージを送ってから新規作成してね！" if has_empty_chat else None
        ):
            self._create_new_chat()
            st.rerun()
        
        st.sidebar.divider()
        
        # チャット一覧
        for chat in chat_list:
            if st.sidebar.button(f"{chat['title']}", key=f"link_{chat['id']}"):
                self._update_current_chat(chat["id"])
                st.rerun()
        
        # RAG設定セクション
        if self.rag_manager:
            st.sidebar.divider()
            st.sidebar.subheader("📚 RAG設定")
            
            status = self.rag_manager.get_status()
            
            if "previous_threshold" not in st.session_state:
                st.session_state.previous_threshold = status['threshold']
            
            # 閾値スライダー
            new_threshold = st.sidebar.slider(
                "閾値",
                min_value=MIN_VALUE,
                max_value=MAX_VALUE,
                value=status['threshold'],
                step=STEP,
                help="値が小さいほど厳密にマッチします。推奨は1.0〜2.0です。"
            )
            
            if new_threshold != st.session_state.previous_threshold:
                self.rag_manager.threshold = new_threshold
                st.session_state.previous_threshold = new_threshold
                st.toast(f"閾値を {new_threshold} に更新しました", icon="✅")
            
            # 資料格納先リンク
            if GOOGLE_DRIVE_FOLDER_URL:
                st.sidebar.markdown(
                    f"📁 [**資料格納先に移動**]({GOOGLE_DRIVE_FOLDER_URL})",
                    unsafe_allow_html=True
                )
    
    def _create_new_chat(self):
        """新しいチャットをメモリ上に作成（Firestoreには最初のメッセージ送信時に保存）"""
        new_title = "新規チャット"
        new_id = shortuuid.uuid()
        new_chat = {"id": new_id, "title": new_title}
        
        # ChatManagerの内部データを更新
        self.chat_manager.chat_list.insert(0, new_chat)
        self.chat_manager.all_chat_histories[new_id] = []
        
        # session_stateに同期
        st.session_state.chat_list = self.chat_manager.chat_list
        st.session_state.all_chat_histories = self.chat_manager.all_chat_histories
        
        self._update_current_chat(new_id)
    
    def _render_chat_title(self):
        """選択中のチャットのタイトルを表示（新規チャットは非表示）"""
        selected_title = self.chat_manager.get_chat_title_by_id(
            st.session_state.current_chat["id"]
        )
        if not selected_title.startswith("新規チャット"):
            st.subheader(f"📂 {selected_title}")
    
    def _render_chat_history(self):
        """チャットの会話履歴を表示"""
        chat_histories = self.chat_manager.get_chat_histories(
            st.session_state.current_chat["id"]
        )

        for chat in chat_histories:
            with st.chat_message(chat["role"]):
                st.markdown(chat["content"])

                if chat["role"] == "assistant":
                    self._render_response_mode_info(chat)
    
    def _render_response_mode_info(self, chat: Dict[str, Any]):
        """AI応答のモード情報（RAG/通常）を表示"""
        if chat.get("is_rag") and chat.get("chunks"):
            st.info("📚 **RAGモード**: 資料を参照して回答を生成しました")
            with st.expander("📖 参照した資料の詳細を見る", expanded=False):
                for i, chunk in enumerate(chat["chunks"], 1):
                    source = chunk.get('source', '不明')
                    drive_link = self.rag_manager.get_google_drive_link(source) if self.rag_manager else ""
                    
                    if drive_link:
                        st.markdown(f"**[{i}]** [{source}]({drive_link}) 📄")
                    else:
                        st.markdown(f"**[{i}]** {source}")

                    score = chunk.get('distance', 0)
                    st.markdown(f"**類似度スコア**: {score:.4f} (スコアが低いほど関連性が高い)")

                    if i < len(chat["chunks"]):
                        st.divider()
        else:
            st.info("💬 **通常モード**: RAG資料に関連情報がないため、一般知識で回答しました")
    
    def _render_chat_input(self):
        """チャット入力欄を表示し、ユーザー入力を処理"""
        user_input = st.chat_input("送信するメッセージを入力")

        if not user_input:
            return

        with st.chat_message("user"):
            st.markdown(user_input)

        self._add_user_message(user_input)
        self._process_ai_response(user_input)
        
        if self._auto_generate_title_if_needed():
            st.rerun()

    def _process_ai_response(self, user_input: str):
        """RAG使用有無を判断し、AIの回答を生成して表示"""
        current_id = st.session_state.current_chat["id"]

        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            use_rag = False
            rag_context = ""
            search_results = []
            rag_data = {}

            # RAG検索
            if self.rag_manager:
                message_placeholder.markdown("🔍 関連資料を検索中...")
                rag_data = self.rag_manager.get_rag_response_data(user_input)
                use_rag = rag_data["use_rag"]
                rag_context = rag_data.get("context", "")
                search_results = rag_data.get("search_results", [])

            # 回答生成
            full_response = ""

            if use_rag and rag_context:
                message_placeholder.markdown("📚 資料を参照して回答を生成中...")
                full_response = self._generate_rag_response(
                    current_id, rag_data["prompt"], message_placeholder
                )
            else:
                message_placeholder.markdown("🤔 AIが考え中だよ...ちょっと待ってね!")
                full_response = self._generate_normal_response(
                    current_id, message_placeholder
                )

            # モード表示
            self._render_search_results(use_rag, search_results)

        # Firestore保存
        chunks_to_save = self._format_chunks_for_save(search_results) if use_rag and search_results else None
        self._add_ai_message(full_response, is_rag=use_rag, chunks=chunks_to_save)
    
    def _generate_rag_response(self, current_id: str, rag_prompt: str, placeholder) -> str:
        """RAGモードで回答を生成"""
        chat_histories = self.chat_manager.get_chat_histories(current_id)
        formatted_messages = self.chat_manager.format_chat_histories(chat_histories[:-1])
        formatted_messages.append(self.langchain_manager.create_human_message(rag_prompt))

        full_response = ""
        for chunk in self.langchain_manager.get_streaming_response_rag(formatted_messages):
            full_response += chunk
            placeholder.markdown(full_response)
        
        return full_response
    
    def _generate_normal_response(self, current_id: str, placeholder) -> str:
        """通常モードで回答を生成"""
        chat_histories = self.chat_manager.get_chat_histories(current_id)
        formatted_messages = self.chat_manager.format_chat_histories(chat_histories)

        full_response = ""
        for chunk in self.langchain_manager.get_streaming_response(formatted_messages):
            full_response += chunk
            placeholder.markdown(full_response)
        
        return full_response
    
    def _render_search_results(self, use_rag: bool, search_results: List[Dict[str, Any]]):
        """検索結果のモード情報を表示"""
        if use_rag and search_results:
            st.info("📚 **RAGモード**: 資料を参照して回答を生成しました")
            with st.expander("📖 参照した資料の詳細を見る", expanded=False):
                for i, doc in enumerate(search_results, 1):
                    source = doc['metadata'].get('source', '不明')
                    page = doc['metadata'].get('page', '?')
                    drive_link = self.rag_manager.get_google_drive_link(source)
                    
                    if drive_link:
                        st.markdown(f"**[{i}]** [{source}]({drive_link}) (ページ {page}) 📄")
                    else:
                        st.markdown(f"**[{i}]** {source} (ページ {page})")
                    
                    st.markdown(f"> {doc['text'][:200]}...")
                    st.markdown(f"**類似度スコア**: {doc['distance']:.4f} (スコアが低いほど関連性が高い)")
                    
                    if i < len(search_results):
                        st.divider()
        else:
            st.info("💬 **通常モード**: RAG資料に関連情報がないため、一般知識で回答しました")
    
    def _format_chunks_for_save(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """検索結果をFirestore保存用の形式に変換"""
        return [
            {
                "chunk_id": f"{doc['metadata'].get('source', '')}_{doc['metadata'].get('page', '')}_{doc['metadata'].get('chunk_index', '')}",
                "distance": doc['distance'],
                "source": doc['metadata'].get('source', '不明')
            }
            for doc in search_results
        ]

    def run(self):
        """アプリケーションのメイン実行"""
        self._render_title()
        self._render_sidebar()
        self._render_chat_title()
        self._render_chat_history()
        self._render_chat_input()