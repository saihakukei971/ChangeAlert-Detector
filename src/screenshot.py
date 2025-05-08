"""
スクリーンショット機能を提供するモジュール
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

from logger import get_logger

logger = get_logger()

async def take_screenshot_async(url, output_path, config):
    """
    指定されたURLのスクリーンショットを非同期で取得する関数

    Args:
        url (str): スクリーンショットを取得するURL
        output_path (Path): スクリーンショットの保存パス
        config (dict): スクリーンショット設定

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        async with async_playwright() as p:
            # ブラウザの起動
            browser = await p.chromium.launch()

            # ページの作成
            page = await browser.new_page()

            # ビューポートサイズの設定
            width = config.get('width', 1280)
            height = config.get('height', 800)
            await page.set_viewport_size({"width": width, "height": height})

            # URLに移動
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # スクリーンショットの保存
            await page.screenshot(path=output_path, full_page=True)

            # ブラウザのクローズ
            await browser.close()

            logger.debug(f"Screenshot saved to {output_path}")
            return True
    except Exception as e:
        logger.error(f"Error taking screenshot of {url}: {e}")
        return False

def take_screenshot(url, output_dir, config):
    """
    指定されたURLのスクリーンショットを取得する関数（同期ラッパー）

    Args:
        url (str): スクリーンショットを取得するURL
        output_dir (Path): スクリーンショットの保存ディレクトリ
        config (dict): スクリーンショット設定

    Returns:
        str: 保存されたスクリーンショットのパス、失敗した場合は空文字列
    """
    try:
        # 出力パスの作成
        from utils import get_timestamp
        timestamp = get_timestamp()
        file_format = config.get('format', 'png')
        output_path = output_dir / f"screenshot_{timestamp}.{file_format}"

        # 非同期関数の実行
        success = asyncio.run(take_screenshot_async(url, output_path, config))

        if success:
            return str(output_path)
        return ""
    except Exception as e:
        logger.error(f"Error in screenshot wrapper for {url}: {e}")
        return ""