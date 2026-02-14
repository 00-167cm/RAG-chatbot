"""
🔵 langchain_managerの役割
    AIとの連携(ユーザーの入力渡すことから、AIの返答返すまで)
    chat_managerから受け取ったユーザーの入力をAIに渡す
    AIの回答を取得
    AIの回答をchat_managerに返す
    会話内容からタイトルを生成
    
【更新履歴】
- RAGモード用のプロンプトとレスポンス生成を追加
"""
# LangChainのOpenAI接続クラス
from langchain_openai import ChatOpenAI
# プロンプト管理
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# 出力を文字列に変換
from langchain_core.output_parsers import StrOutputParser
# メッセージ型
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
# 型ヒント用
from typing import List, Generator

from config.settings import OPENAI_MODEL, TEMPERATURE, TITLE_MAX_LENGTH, SYSTEM_PROMPT_NORMAL, SYSTEM_PROMPT_RAG, SYSTEM_PROMPT_TITLE

class LangChainManager:
    """
    LangChainを使ったAI連携を管理するクラス
    初期化した時に引数を与えていないから、model,temperatureはデフォルト引数が適用される
    """
    def __init__(self, model: str = OPENAI_MODEL, temperature: float = TEMPERATURE):
        """
        OpenAIとの連携を設定する
            
        【初期化で行うこと】
        1. モデルと温度パラメータを設定
        2. ChatOpenAIクライアントを作成
        3. プロンプトテンプレートを準備
        4. 応答チェーンを構築
            
        Args:
            model: 使用するOpenAIモデル名
            temperature: 応答の多様性（0.0〜1.0）
        """
        self.model = model
        self.temperature = temperature

        # 関数名の頭につく「_」はそのクラス内からしか呼び出されないことを表すマナー(ルールではない)
        # 2._initialize_llm() を呼び出してLLMを初期化
        self.llm = self._initialize_llm()
        # → ChatOpenAI(model="gpt-4o-mini", temperature=0.7) が実行される
        # → OpenAIに接続できる状態になる

        # 3. プロンプトテンプレートを作成
        self.prompt = self._create_prompt()
        # → ChatPromptTemplate.from_messages([...]) が実行される
        # → システムプロンプトとMessagesPlaceholderが設定される

        # 4. 出力パーサーを初期化(AIの応答を文字列に変換するためのもの)
        self.output_parser = StrOutputParser()
        # 5. これらを組み合わせてチェーンを作成(prompt → llm → output_parser の順で処理が流れる)
        # |(パイプ)演算子でつなぐことで、データが順番に流れていく
        self.chain = self.prompt | self.llm | self.output_parser
        
        # タイトル生成用のチェーンも作成
        self.title_prompt = self._create_title_prompt()
        self.title_chain = self.title_prompt | self.llm | self.output_parser
        
        # 🆕 RAG用のプロンプトとチェーンを作成
        self.rag_prompt = self._create_rag_prompt()
        self.rag_chain = self.rag_prompt | self.llm | self.output_parser
    
    def _initialize_llm(self) -> ChatOpenAI:
        """
        LLM(Large Language Model)の初期化

        Returns:
        ChatOpenAIのインスタンス(AIとの接続オブジェクト)
        
        【補足】
        -> ChatOpenAI は「この関数の戻り値の型」を示す型ヒント
        実際の動作には影響しないが、コードを読む人に分かりやすくするため
        """
        return ChatOpenAI(
            model=self.model,
            temperature=self.temperature
        )
    
    def _create_prompt(self) -> ChatPromptTemplate:
        # インスタンス化したChatPromptTemplateを返す「だけ」
        # クラスの中に関数がある      
        """
        プロンプトテンプレートの作成

        Returns:
        ChatPromptTemplateのインスタンス
        """

        return ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT_NORMAL),
            MessagesPlaceholder(variable_name="messages")
        ])
    
    def _create_title_prompt(self) -> ChatPromptTemplate:
        """
        タイトル生成用のプロンプトテンプレートを作成
        
        Returns:
        ChatPromptTemplateのインスタンス
        """

        return ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT_TITLE),
            MessagesPlaceholder(variable_name="messages")
        ])
    
    def _create_rag_prompt(self) -> ChatPromptTemplate:
        """
        RAG用のプロンプトテンプレートを作成
        
        Returns:
        ChatPromptTemplateのインスタンス
        """

        return ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT_RAG),
            MessagesPlaceholder(variable_name="messages")
        ])
    
    def create_human_message(self, content: str) -> HumanMessage:
        """
        ユーザーの入力からHumanMessageオブジェクトを作成
        
        Args:
            content: ユーザーの入力テキスト(例: "こんにちは")
        
        Returns:
            HumanMessage: LangChain用のメッセージオブジェクト

        """
        return HumanMessage(content=content)
    
    def create_ai_message(self, content: str) -> AIMessage:
        """
        AIの応答からAIMessageオブジェクトを作成
        
        Args:
            content: AIの応答テキスト(例: "こんにちは!調子はどう?")
        
        Returns:
            AIMessage: LangChain用のメッセージオブジェクト

        """
        # AIMessageクラスをインスタンス化
        # contentを引数として渡すと、AIの応答として扱われる
        return AIMessage(content=content)
    
    def get_streaming_response(
        self,
        messages: List
    ) -> Generator[str, None, None]:
        """
        メッセージ履歴を基にAIからストリーミング応答を取得
        
        Args:
            messages: LangChain形式のメッセージ履歴リスト
                [HumanMessage(...), AIMessage(...), ...]
        """
        for chunk in self.chain.stream({"messages": messages}):
            yield chunk
    
    def get_streaming_response_rag(
        self,
        messages: List
    ) -> Generator[str, None, None]:
        """
        🆕 RAGモード用のストリーミング応答を取得
        
        Args:
            messages: LangChain形式のメッセージ履歴リスト
                      （RAGプロンプトを含む）
        
        Yields:
            str: AIからの応答チャンク
        """
        for chunk in self.rag_chain.stream({"messages": messages}):
            yield chunk
    
    def get_complete_response(
        self,
        messages: List
    ) -> str:
        """
        メッセージ履歴を基にAIから完全な応答を取得
        (ストリーミングではなく一度に取得)
        
        Args:
            messages: LangChain形式のメッセージ履歴リスト
        
        Returns:
            str: AIからの完全な応答(例: "こんにちは!調子はどう?")
        
        【get_streaming_response()との違い】
        - get_streaming_response: 1文字ずつ返す(リアルタイム表示向け)
        - get_complete_response: 全文を一気に返す(バッチ処理向け)
        """
        return self.chain.invoke({"messages": messages})
    
    def generate_title(self, messages: List) -> str:
        """
        会話内容からタイトルを生成
        
        Args:
            messages: LangChain形式のメッセージ履歴リスト(最初の数件)
        
        Returns:
            生成されたタイトル(15文字以内)
        """
        # タイトル生成チェーンを実行
        title = self.title_chain.invoke({"messages": messages})
        
        # 余計な空白や改行を削除
        title = title.strip()

        if len(title) > TITLE_MAX_LENGTH:
            title = title[:TITLE_MAX_LENGTH]
        
        return title