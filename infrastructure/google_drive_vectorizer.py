"""
☁️ Google Drive取り込み
    Google Driveからファイルを取得しチャンク化する
"""
import logging
import shutil
from typing import List, Dict, Optional
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from infrastructure.document_processor import DocumentProcessor
from config.settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    GD_FOLDER_ID
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GoogleDriveVectorizer:
    """
    Google Drive取り込みクラス
    """

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    # 通常ファイルの対応形式（拡張子 → 処理メソッド名）
    SUPPORTED_EXTENSIONS = {
        ".pdf": "process_pdf",
        ".html": "process_html",
        ".xlsx": "process_excel",
        ".docx": "process_word",
        ".pptx": "process_pptx",
    }

    # Googleネイティブ形式のエクスポート定義
    # MIMEタイプ → (エクスポート先MIMEタイプ, 変換後の拡張子)
    GOOGLE_NATIVE_EXPORT = {
        "application/vnd.google-apps.spreadsheet": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx"
        ),
        "application/vnd.google-apps.document": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx"
        ),
        "application/vnd.google-apps.presentation": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx"
        ),
    }

    def __init__(
        self,
        service_account_path: str = "secrets/gc_service_account.json"
    ):
        """
        Args:
            service_account_path: サービスアカウントのJSONファイルパス
        """
        self.service_account_path = Path(service_account_path)

        creds = service_account.Credentials.from_service_account_file(
            str(self.service_account_path),
            scopes=self.SCOPES
        )
        self.drive_service = build("drive", "v3", credentials=creds)

        self.document_processor = DocumentProcessor(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

    def _list_files(self, folder_id: str) -> List[Dict[str, str]]:
        """
        指定フォルダ内のファイル一覧を取得

        Args:
            folder_id: Google DriveのフォルダID

        Returns:
            ファイル情報のリスト [{"id": "xxx", "name": "xxx", "url": "xxx", "mimeType": "xxx"}, ...]
        """
        results = self.drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name, webViewLink, mimeType)"
        ).execute()

        files = []
        for f in results.get("files", []):
            files.append({
                "id": f["id"],
                "name": f["name"],
                "url": f.get("webViewLink", ""),
                "mimeType": f.get("mimeType", "")
            })

        logger.info(f"📂 Google Driveフォルダ内のファイル: {len(files)}件")
        for f in files:
            logger.info(f"   - {f['name']} ({f['mimeType']})")

        return files

    def _download_file(
        self,
        file_id: str,
        file_name: str,
        mime_type: str = ""
    ) -> Optional[Path]:
        """
        Google Driveからファイルをダウンロードしてローカルのtmpに保存
        Googleネイティブ形式の場合はexport_media()でOffice形式に変換する

        Args:
            file_id: Google DriveのファイルID
            file_name: ファイル名
            mime_type: ファイルのMIMEタイプ

        Returns:
            ダウンロードしたファイルのパス（失敗時はNone）
        """
        try:
            tmp_dir = Path("data/tmp_gdrive")
            tmp_dir.mkdir(parents=True, exist_ok=True)

            # Googleネイティブ形式の場合はエクスポート変換
            if mime_type in self.GOOGLE_NATIVE_EXPORT:
                export_mime, export_ext = self.GOOGLE_NATIVE_EXPORT[mime_type]
                save_name = f"{Path(file_name).stem}{export_ext}"
                tmp_path = tmp_dir / save_name

                request = self.drive_service.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime
                )

                with open(tmp_path, "wb") as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()

                logger.info(f"⬇️ エクスポート完了（{mime_type} → {export_ext}）: {save_name}")
                return tmp_path

            # 通常ファイルはそのままダウンロード
            tmp_path = tmp_dir / file_name

            request = self.drive_service.files().get_media(fileId=file_id)

            with open(tmp_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            logger.info(f"⬇️ ダウンロード完了: {file_name}")
            return tmp_path

        except Exception as e:
            logger.error(f"❌ ダウンロード失敗 ({file_name}): {e}")
            return None

    def _get_processor_method(self, file_name: str):
        """
        ファイル名の拡張子から対応する処理メソッドを返す

        Args:
            file_name: ファイル名

        Returns:
            処理メソッド（対応外の拡張子はNone）
        """
        ext = Path(file_name).suffix.lower()
        method_name = self.SUPPORTED_EXTENSIONS.get(ext)

        if method_name is None:
            return None

        return getattr(self.document_processor, method_name)

    def _is_supported(self, file_name: str, mime_type: str) -> bool:
        """
        ファイルが処理対象かどうかを判定する

        Args:
            file_name: ファイル名
            mime_type: MIMEタイプ

        Returns:
            処理対象ならTrue
        """
        if mime_type in self.GOOGLE_NATIVE_EXPORT:
            return True

        ext = Path(file_name).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def get_chunks(self, folder_id: str = None) -> list:
        """
        Google Driveフォルダ内の全対応ファイルを処理してチャンクを返す（DB保存はしない）

        Args:
            folder_id: GoogleドライブのフォルダID（省略時はsettings.pyのGD_FOLDER_ID）

        Returns:
            チャンクのリスト
        """
        folder_id = folder_id or GD_FOLDER_ID

        if not folder_id:
            logger.error("❌ GD_FOLDER_IDが設定されていません")
            return []

        if not self.service_account_path.exists():
            logger.error(f"❌ サービスアカウントファイルが見つかりません: {self.service_account_path}")
            return []

        files = self._list_files(folder_id)
        if not files:
            logger.warning("⚠️ フォルダ内にファイルがありません")
            return []

        all_chunks = []
        skip_count = 0

        for file_info in files:
            file_name = file_info["name"]
            drive_url = file_info["url"]
            mime_type = file_info["mimeType"]

            if not self._is_supported(file_name, mime_type):
                ext = Path(file_name).suffix.lower()
                supported = ", ".join(self.SUPPORTED_EXTENSIONS.keys())
                logger.info(
                    f"⏭️ スキップ（非対応形式 '{ext}'）: {file_name}"
                    f"（対応形式: {supported} + Googleネイティブ形式）"
                )
                skip_count += 1
                continue

            tmp_path = self._download_file(file_info["id"], file_name, mime_type)
            if not tmp_path:
                continue

            processor = self._get_processor_method(tmp_path.name)
            if processor is None:
                logger.warning(f"⚠️ 処理メソッドが見つかりません: {tmp_path.name}")
                tmp_path.unlink(missing_ok=True)
                skip_count += 1
                continue

            chunks = processor(str(tmp_path))

            for chunk in chunks:
                chunk["metadata"]["drive_url"] = drive_url

            all_chunks.extend(chunks)
            logger.info(f"✅ {tmp_path.name}: {len(chunks)}チャンク作成")

            tmp_path.unlink(missing_ok=True)

        tmp_dir = Path("data/tmp_gdrive")
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)

        logger.info(f"📊 処理結果: {len(all_chunks)}チャンク生成, {skip_count}件スキップ")

        return all_chunks