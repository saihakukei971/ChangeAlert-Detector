"""
メインの監視ロジックを提供するモジュール
"""
import os
import time
import json
import csv
import hashlib
from datetime import datetime
from pathlib import Path
import pandas as pd

from utils import (
    load_config,
    load_urls,
    check_date_condition,
    get_page_content,
    generate_hash,
    detect_changes,
    create_report_dirs,
    get_timestamp
)
from screenshot import take_screenshot
from notifier import send_notification
from visualizer import create_monitoring_report
from logger import setup_logger, get_logger

def initialize():
    """
    監視ツールの初期化を行う関数

    Returns:
        tuple: (設定辞書, 監視対象URLリスト, ロガー)
    """
    try:
        # 設定の読み込み
        config = load_config()

        # ロガーのセットアップ
        logger = setup_logger(config.get('log', {'level': 'INFO'}))

        # 監視対象URLの読み込み
        urls = load_urls()

        logger.info("Web Monitor initialized")
        return config, urls, logger

    except Exception as e:
        print(f"Error during initialization: {e}")
        return {}, [], None

def load_url_history(url):
    """
    URLの監視履歴を読み込む関数

    Args:
        url (str): URL

    Returns:
        str: 前回の内容のハッシュ
    """
    try:
        history_dir = Path('data/history')
        history_dir.mkdir(parents=True, exist_ok=True)

        # URLからファイル名を生成
        url_hash = hashlib.md5(url.encode()).hexdigest()
        history_file = history_dir / f"{url_hash}.json"

        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as file:
                history = json.load(file)
                return history.get('last_hash', ''), history.get('last_content', '')

        return '', ''

    except Exception as e:
        logger = get_logger()
        logger.error(f"Error loading history for {url}: {e}")
        return '', ''

def save_url_history(url, content_hash, content):
    """
    URLの監視履歴を保存する関数

    Args:
        url (str): URL
        content_hash (str): コンテンツのハッシュ
        content (str): コンテンツ

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        history_dir = Path('data/history')
        history_dir.mkdir(parents=True, exist_ok=True)

        # URLからファイル名を生成
        url_hash = hashlib.md5(url.encode()).hexdigest()
        history_file = history_dir / f"{url_hash}.json"

        history = {
            'url': url,
            'last_hash': content_hash,
            'last_content': content,
            'last_checked': datetime.now().isoformat()
        }

        with open(history_file, 'w', encoding='utf-8') as file:
            json.dump(history, file, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        logger = get_logger()
        logger.error(f"Error saving history for {url}: {e}")
        return False

def save_monitoring_result(result, csv_dir):
    """
    監視結果をCSVに保存する関数

    Args:
        result (dict): 監視結果
        csv_dir (Path): CSVの保存先ディレクトリ

    Returns:
        str: 保存したCSVのパス
    """
    try:
        timestamp = get_timestamp()
        csv_path = csv_dir / f"report_{timestamp}.csv"

        # CSVに変換可能なデータを作成
        csv_data = {
            'timestamp': [],
            'url': [],
            'name': [],
            'status_code': [],
            'has_changed': [],
            'screenshot_path': []
        }

        for url_info in result:
            csv_data['timestamp'].append(url_info['timestamp'])
            csv_data['url'].append(url_info['url'])
            csv_data['name'].append(url_info.get('name', ''))
            csv_data['status_code'].append(url_info.get('status_code', 0))
            csv_data['has_changed'].append(url_info.get('has_changed', False))
            csv_data['screenshot_path'].append(url_info.get('screenshot_path', ''))

        # DataFrameを作成してCSVに保存
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_path, index=False)

        logger = get_logger()
        logger.info(f"Monitoring result saved to {csv_path}")

        return str(csv_path)

    except Exception as e:
        logger = get_logger()
        logger.error(f"Error saving monitoring result: {e}")
        return ""

def monitor_url(url_info, config, csv_dir, picture_dir):
    """
    単一のURLを監視する関数

    Args:
        url_info (dict): URL情報
        config (dict): 設定辞書
        csv_dir (Path): CSVの保存先ディレクトリ
        picture_dir (Path): 画像の保存先ディレクトリ

    Returns:
        dict: 監視結果
    """
    logger = get_logger()
    result = {
        'url': url_info['url'],
        'name': url_info.get('name', ''),
        'timestamp': datetime.now().isoformat(),
        'has_changed': False,
        'status_code': 0,
        'screenshot_path': ''
    }

    try:
        logger.info(f"Monitoring URL: {url_info['url']}")

        # 過去の履歴を読み込む
        last_hash, last_content = load_url_history(url_info['url'])

        # ページの内容を取得
        content = get_page_content(url_info['url'])

        if not content:
            logger.error(f"Failed to fetch content from {url_info['url']}")
            return result

        # ハッシュを生成
        content_hash = generate_hash(content)

        # 変更を検出
        has_changed, diff = detect_changes(last_content, content)
        result['has_changed'] = has_changed

        if has_changed:
            logger.info(f"Changes detected on {url_info['url']}")

            # スクリーンショットの設定があれば撮影
            if config.get('screenshot', {}).get('enabled', False):
                screenshot_path = take_screenshot(
                    url_info['url'],
                    picture_dir,
                    config.get('screenshot', {})
                )
                result['screenshot_path'] = screenshot_path

            # 通知を送信
            if config.get('notifications', {}).get('diff_only', True) and diff:
                send_notification(
                    url_info,
                    diff,
                    config.get('notifications', {}),
                    result.get('screenshot_path', '')
                )

        # 履歴を保存
        save_url_history(url_info['url'], content_hash, content)

        return result

    except Exception as e:
        logger.error(f"Error monitoring {url_info['url']}: {e}")
        return result

def run_monitoring():
    """
    監視プロセスを実行するメイン関数
    """
    # 初期化
    config, urls, logger = initialize()

    if not logger:
        print("Failed to initialize logger")
        return

    if not urls:
        logger.error("No URLs found for monitoring")
        return

    # 日付条件のチェック
    if not check_date_condition(config):
        logger.info("Current date is outside the monitoring period")
        return

    # レポートディレクトリの作成
    csv_dir, picture_dir = create_report_dirs()

    # 各URLを監視
    monitoring_results = []

    for url_info in urls:
        result = monitor_url(url_info, config, csv_dir, picture_dir)
        monitoring_results.append(result)

    # 結果の保存
    csv_path = save_monitoring_result(monitoring_results, csv_dir)

    # 視覚化
    if config.get('report', {}).get('visualization_enabled', False):
        chart_type = config.get('report', {}).get('chart_type', 'all')
        create_monitoring_report(picture_dir, chart_type)

    logger.info("Monitoring completed")

if __name__ == "__main__":
    run_monitoring()