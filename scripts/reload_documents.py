"""
reload_documents.py
Google Driveから最新のドキュメントを取得し、ベクトルデータベースを再構築するスクリプト

【処理フロー】
1. settings.pyからGoogle DriveのURLを取得
2. URLからフォルダIDを抽出
3. ChromaDBの既存データをクリア
4. Drive API経由でメモリ上でファイルを処理・ベクトル化
"""
import os
import re
from dotenv import load_dotenv
from infrastructure.google_drive_vectorizer import GoogleDriveVectorizer
from config.settings import CHROMA_DB_PATH, COLLECTION_NAME, GOOGLE_DRIVE_FOLDER_URL

# 環境変数のロード
load_dotenv()

def get_folder_id_from_url(url: str) -> str:
    """Google DriveのURLからフォルダIDを抽出する"""
    if not url:
        return None
    # folders/の後ろにある文字列を取得する正規表現
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None

def main():
    print("=" * 50)
    print("☁️ Google Drive → RAG System 同期ツール")
    print("=" * 50)

    # 1. 認証ファイルのチェック
    if not os.path.exists("credentials.json"):
        print("❌ エラー: 'credentials.json' が見つかりません。")
        print("プロジェクトのルートディレクトリに配置してください。")
        return

    # 2. フォルダIDの取得
    folder_id = get_folder_id_from_url(GOOGLE_DRIVE_FOLDER_URL)
    
    if not folder_id:
        print("❌ エラー: Google DriveのフォルダIDが特定できませんでした。")
        print(f"設定されたURL: {GOOGLE_DRIVE_FOLDER_URL}")
        print(".env または config/settings.py を確認してください。")
        return

    print(f"🎯 ターゲットフォルダID: {folder_id}")

    # 3. Vectorizerの初期化
    vectorizer = GoogleDriveVectorizer(
        credentials_path="credentials.json",
        token_path="google_token.json", # 自動生成されます
        persist_directory=CHROMA_DB_PATH,
        collection_name=COLLECTION_NAME
    )

    # 4. 既存データのクリア（完全リロード）
    print("\n🔄 既存のナレッジベースをクリア中...")
    vectorizer.clear_collection()

    # 5. 同期実行
    print(f"\n📥 Google Driveから同期を開始...")
    success = vectorizer.process_folder(
        folder_id=folder_id,
        recursive=True  # サブフォルダも読み込む
    )

    if success:
        print("\n" + "=" * 50)
        print("✅ 同期完了！最新のデータがRAGシステムに反映されました。")
        print("=" * 50)
        print("Next Step: 'streamlit run main.py' でチャットボットを起動してください。")
    else:
        print("\n❌ 同期に失敗しました。ログを確認してください。")

if __name__ == "__main__":
    main()