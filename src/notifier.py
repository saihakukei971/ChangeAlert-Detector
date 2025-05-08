"""
通知機能を提供するモジュール
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from logger import get_logger

# 環境変数の読み込み
load_dotenv(Path('config/.env'))
logger = get_logger()

def send_email_notification(url_info, diff, screenshot_path=None):
    """
    メール通知を送信する関数

    Args:
        url_info (dict): URL情報の辞書
        diff (str): 検出された差分
        screenshot_path (str, optional): スクリーンショットのパス

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        # SMTP設定の取得
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')

        # メール送信元と宛先
        sender = os.environ.get('EMAIL_FROM')
        recipients_str = os.environ.get('EMAIL_RECIPIENTS', '')
        recipients = [email.strip() for email in recipients_str.split(',') if email.strip()]

        if not smtp_server or not smtp_username or not smtp_password or not sender or not recipients:
            logger.error("Missing email configuration in .env file")
            return False

        # URLの名前があれば使用、なければURLを使用
        site_name = url_info.get('name', url_info['url'])

        # メッセージの作成
        msg = MIMEMultipart()
        msg['Subject'] = f"Web Monitor Alert: Changes detected on {site_name}"
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)

        # メール本文の作成
        html_content = f"""
        <html>
        <body>
            <h2>Web Monitor Alert</h2>
            <p>Changes have been detected on the monitored website:</p>
            <ul>
                <li><strong>URL:</strong> <a href="{url_info['url']}">{url_info['url']}</a></li>
                <li><strong>Name:</strong> {site_name}</li>
                <li><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>

            <h3>Detected Changes:</h3>
            <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">{diff}</pre>

            {f'<h3>Screenshot:</h3><p>See attachment</p>' if screenshot_path else ''}

            <p>This is an automated notification from Web Monitor.</p>
        </body>
        </html>
        """

        # HTMLパートの追加
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # スクリーンショットの添付
        if screenshot_path:
            try:
                with open(screenshot_path, 'rb') as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_path))
                    msg.attach(img)
            except Exception as e:
                logger.error(f"Error attaching screenshot: {e}")

        # SMTPサーバーに接続してメール送信
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info(f"Email notification sent for {url_info['url']} to {len(recipients)} recipients")
        return True

    except Exception as e:
        logger.error(f"Error sending email notification: {e}")
        return False

def send_slack_notification(url_info, diff, screenshot_path=None):
    """
    Slack通知を送信する関数

    Args:
        url_info (dict): URL情報の辞書
        diff (str): 検出された差分
        screenshot_path (str, optional): スクリーンショットのパス

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        # Slack Webhook URLの取得
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        channel = os.environ.get('SLACK_CHANNEL', '#website-monitoring')
        username = os.environ.get('SLACK_USERNAME', 'WebMonitor Bot')

        if not webhook_url:
            logger.error("Missing Slack webhook URL in .env file")
            return False

        # URLの名前があれば使用、なければURLを使用
        site_name = url_info.get('name', url_info['url'])

        # メッセージの作成
        message = {
            "channel": channel,
            "username": username,
            "icon_emoji": ":robot_face:",
            "attachments": [
                {
                    "color": "#f2c744",
                    "title": f"Changes detected on {site_name}",
                    "title_link": url_info['url'],
                    "text": f"```{diff[:1000]}{'...' if len(diff) > 1000 else ''}```",
                    "fields": [
                        {
                            "title": "URL",
                            "value": url_info['url'],
                            "short": False
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "Web Monitor",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

        # スクリーンショットをアップロードする場合の処理は省略
        # 実際の実装ではSlackのファイルアップロードAPIを使用する必要がある

        # Webhookにメッセージを送信
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()

        logger.info(f"Slack notification sent for {url_info['url']}")
        return True

    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        return False

def send_notification(url_info, diff, config, screenshot_path=None):
    """
    設定に基づいて通知を送信する関数

    Args:
        url_info (dict): URL情報の辞書
        diff (str): 検出された差分
        config (dict): 通知設定
        screenshot_path (str, optional): スクリーンショットのパス

    Returns:
        bool: いずれかの通知が成功した場合はTrue
    """
    success = False

    # URLごとの通知設定をチェック
    should_notify = url_info.get('notification', 'true').lower() == 'true'

    if not should_notify:
        logger.debug(f"Notification disabled for {url_info['url']}")
        return False

    # メール通知
    if config.get('email', False):
        email_success = send_email_notification(url_info, diff, screenshot_path)
        success = success or email_success

    # Slack通知
    if config.get('slack', False):
        slack_success = send_slack_notification(url_info, diff, screenshot_path)
        success = success or slack_success

    return success