"""
ロギング機能を提供するモジュール
"""
import os
import sys
from datetime import datetime
from pathlib import Path
import json

from loguru import logger

def setup_logger(config):
    """
    loguruを使用してログ設定を行う関数

    Args:
        config (dict): ログ設定を含む辞書
    """
    # ログレベルの設定
    log_level = config.get('level', 'INFO')

    # ログファイルのパスを作成
    log_dir = Path('logs/Execution_logFolder')
    log_dir.mkdir(parents=True, exist_ok=True)

    # JSONログのディレクトリ作成
    json_log_dir = Path('logs/log_json')
    json_log_dir.mkdir(parents=True, exist_ok=True)

    # 現在の日付を取得してログファイル名を生成
    today = datetime.now().strftime('%Y%m%d')
    log_file = log_dir / f"{today}.log"
    json_log_file = json_log_dir / f"{today}.json"

    # デフォルトのロガーを削除
    logger.remove()

    # 標準出力へのロガーを追加
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # ファイルへのロガーを追加
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention=f"{config.get('retention_days', 30)} days"
    )

    # JSONフォーマットのログが有効な場合、JSON形式でもログを保存（別ディレクトリに）
    if config.get('json_format', False):
        logger.add(
            json_log_file,
            level=log_level,
            format=lambda record: json.dumps({
                "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
                "level": record["level"].name,
                "message": record["message"],
                "module": record["name"],
                "function": record["function"],
                "line": record["line"]
            }) + ",\n",
            rotation="1 day",
            retention=f"{config.get('retention_days', 30)} days",
            # JSON配列形式で出力するための特別な処理
            filter=lambda record: record["extra"].update({"write_json_header": record["elapsed"].total_seconds() < 0.01}),
            enqueue=True
        )

        # JSON配列の開始・終了処理を登録
        @logger.catch
        def setup_json_log():
            # ファイルが存在しない場合は開始括弧を書き込む
            if not json_log_file.exists() or json_log_file.stat().st_size == 0:
                with open(json_log_file, 'w') as f:
                    f.write("[\n")

            # プログラム終了時に終了括弧を書き込む
            import atexit
            def finalize_json_log():
                if json_log_file.exists():
                    with open(json_log_file, 'a') as f:
                        f.write("\n]")
            atexit.register(finalize_json_log)

        setup_json_log()

    logger.info("Logger setup completed")
    return logger

def get_logger():
    """
    設定済みのロガーインスタンスを返す

    Returns:
        Logger: loguruのロガーインスタンス
    """
    return logger