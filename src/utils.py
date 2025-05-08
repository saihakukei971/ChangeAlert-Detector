"""
ユーティリティ関数を提供するモジュール
"""
import os
import json
import hashlib
import difflib
from datetime import datetime, timedelta
from pathlib import Path
import csv
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from logger import get_logger

# 環境変数の読み込み
load_dotenv(Path('config/.env'))
logger = get_logger()

def load_config():
    """
    設定ファイルを読み込む関数

    Returns:
        dict: 設定情報の辞書
    """
    try:
        with open(Path('config/settings.json'), 'r', encoding='utf-8') as file:
            config = json.load(file)
        logger.debug(f"Configuration loaded: {config}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def load_urls():
    """
    監視対象URLをCSVから読み込む関数

    Returns:
        list: 監視対象URLの辞書のリスト
    """
    urls = []
    try:
        with open(Path('config/urls.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                urls.append(row)
        logger.debug(f"Loaded {len(urls)} URLs for monitoring")
        return urls
    except Exception as e:
        logger.error(f"Error loading URLs: {e}")
        return []

def check_date_condition(config):
    """
    現在の日付が監視期間内かをチェックする関数

    Args:
        config (dict): 設定辞書

    Returns:
        bool: 監視期間内であればTrue
    """
    try:
        today = datetime.now().date()
        start_date = datetime.strptime(config['monitoring']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(config['monitoring']['end_date'], '%Y-%m-%d').date()

        is_valid = start_date <= today <= end_date

        if is_valid:
            logger.debug(f"Date condition check passed: {start_date} <= {today} <= {end_date}")
        else:
            logger.info(f"Date condition check failed: {today} is not between {start_date} and {end_date}")

        return is_valid
    except Exception as e:
        logger.error(f"Error checking date condition: {e}")
        return False

def get_page_content(url):
    """
    指定されたURLのページコンテンツを取得する関数

    Args:
        url (str): 取得対象のURL

    Returns:
        str: ページの内容
    """
    try:
        user_agent = os.environ.get('USER_AGENT', 'Mozilla/5.0')
        headers = {'User-Agent': user_agent}

        # プロキシ設定の取得
        proxies = {}
        if os.environ.get('HTTP_PROXY'):
            proxies['http'] = os.environ.get('HTTP_PROXY')
        if os.environ.get('HTTPS_PROXY'):
            proxies['https'] = os.environ.get('HTTPS_PROXY')

        response = requests.get(url, headers=headers, proxies=proxies if proxies else None, timeout=30)
        response.raise_for_status()

        logger.debug(f"Successfully fetched content from {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return ""

def generate_hash(content):
    """
    コンテンツのハッシュ値を生成する関数

    Args:
        content (str): ハッシュ化する内容

    Returns:
        str: SHA-256ハッシュ値
    """
    try:
        # BeautifulSoupでHTMLをパース
        soup = BeautifulSoup(content, 'html.parser')

        # 動的に変わる可能性のある要素を除外
        for element in soup.select('script, style, meta[http-equiv="refresh"], meta[name="viewport"]'):
            element.extract()

        # ハッシュ生成
        clean_content = soup.get_text()
        hash_obj = hashlib.sha256(clean_content.encode())
        hash_value = hash_obj.hexdigest()

        logger.debug(f"Generated hash: {hash_value[:10]}...")
        return hash_value
    except Exception as e:
        logger.error(f"Error generating hash: {e}")
        return ""

def detect_changes(old_content, new_content):
    """
    コンテンツの変更を検出する関数

    Args:
        old_content (str): 以前のコンテンツ
        new_content (str): 新しいコンテンツ

    Returns:
        tuple: (変更があるかのブール値, 変更の差分)
    """
    try:
        if not old_content or not new_content:
            return False, ""

        # BeautifulSoupでHTMLをパース
        old_soup = BeautifulSoup(old_content, 'html.parser')
        new_soup = BeautifulSoup(new_content, 'html.parser')

        # テキストの抽出
        old_text = old_soup.get_text().strip().split('\n')
        new_text = new_soup.get_text().strip().split('\n')

        # difflibを使用して差分を検出
        diff = list(difflib.unified_diff(old_text, new_text, n=3))

        # 差分があるかどうか
        has_changes = len(diff) > 0

        if has_changes:
            logger.debug(f"Changes detected: {len(diff)} diff lines")
        else:
            logger.debug("No changes detected")

        return has_changes, '\n'.join(diff)
    except Exception as e:
        logger.error(f"Error detecting changes: {e}")
        return False, ""

def create_report_dirs():
    """
    レポート保存用のディレクトリを作成する関数

    Returns:
        tuple: (CSVディレクトリのパス, 画像ディレクトリのパス)
    """
    today = datetime.now().strftime('%Y%m%d')
    report_dir = Path(f'reports/{today}')

    csv_dir = report_dir / 'CSV'
    picture_dir = report_dir / 'PICTURE'

    csv_dir.mkdir(parents=True, exist_ok=True)
    picture_dir.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Created report directories: {csv_dir} and {picture_dir}")

    return csv_dir, picture_dir

def get_timestamp():
    """
    現在のタイムスタンプを取得する関数

    Returns:
        str: YYYYMMDDHHMMSSフォーマットのタイムスタンプ
    """
    return datetime.now().strftime('%Y%m%d%H%M%S')