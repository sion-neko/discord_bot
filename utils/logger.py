"""
ロギング設定モジュール

プロジェクト全体で統一されたログ設定を提供します。
"""
import logging
import sys
from pathlib import Path


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

    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # フォーマッターの設定
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

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
