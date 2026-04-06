"""
ロギング設定モジュール

プロジェクト全体で統一されたログ設定を提供します。
- コンソール出力 (stdout)
- ファイル出力 (logs/ ディレクトリ, ローテーション付き)
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# ログファイルの設定
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "bot.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
BACKUP_COUNT = 3  # ローテーションで保持するファイル数

# ログフォーマット
LOG_FORMAT = '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def _ensure_log_dir():
    """ログディレクトリを作成"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str = None) -> logging.Logger:
    """
    ロガーをセットアップして返す

    Args:
        name: ロガー名（Noneの場合はルートロガー）

    Returns:
        設定済みのLoggerインスタンス
    """
    logger = logging.getLogger(name)

    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラー (ローテーション付き)
    try:
        _ensure_log_dir()
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        # ファイル出力に失敗してもコンソール出力は継続
        logger.warning(f"ログファイルの作成に失敗しました: {e}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得する

    Args:
        name: ロガー名

    Returns:
        Loggerインスタンス
    """
    return logging.getLogger(name)
