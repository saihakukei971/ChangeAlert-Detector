"""
視覚化機能を提供するモジュール
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
import matplotlib.dates as mdates

from logger import get_logger

logger = get_logger()

def load_monitoring_data(days=30):
    """
    過去の監視データを読み込む関数

    Args:
        days (int): 読み込む日数

    Returns:
        pandas.DataFrame: 監視データのデータフレーム
    """
    try:
        # 過去n日分のCSVファイルを検索
        all_data = []
        reports_dir = Path('reports')

        # 対象となる日付のリストを生成
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            csv_dir = reports_dir / date_str / 'CSV'

            if csv_dir.exists():
                for csv_file in csv_dir.glob('*.csv'):
                    try:
                        df = pd.read_csv(csv_file)
                        all_data.append(df)
                    except Exception as e:
                        logger.error(f"Error reading CSV file {csv_file}: {e}")

            current_date += timedelta(days=1)

        if not all_data:
            logger.warning(f"No monitoring data found for the last {days} days")
            return pd.DataFrame()

        # データの結合
        combined_data = pd.concat(all_data, ignore_index=True)

        # タイムスタンプを日時型に変換
        if 'timestamp' in combined_data.columns:
            combined_data['timestamp'] = pd.to_datetime(combined_data['timestamp'])

        logger.debug(f"Loaded monitoring data: {len(combined_data)} records")
        return combined_data

    except Exception as e:
        logger.error(f"Error loading monitoring data: {e}")
        return pd.DataFrame()

def create_changes_timeline(data, output_path):
    """
    変更頻度のタイムラインを作成する関数

    Args:
        data (pandas.DataFrame): 監視データのデータフレーム
        output_path (Path): 出力パス

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        if data.empty:
            logger.warning("No data available for visualization")
            return False

        # 変更があったデータのみ抽出
        changes_data = data[data['has_changed'] == True].copy()

        if changes_data.empty:
            logger.warning("No changes detected in the data")
            return False

        # URLごとにグループ化
        grouped = changes_data.groupby(['url', pd.Grouper(key='timestamp', freq='D')])
        changes_count = grouped.size().reset_index(name='count')

        # プロットの設定
        plt.figure(figsize=(12, 8))
        sns.set(style="whitegrid")

        # マークサイズを変更回数に比例させる
        ax = sns.scatterplot(
            data=changes_count,
            x='timestamp',
            y='url',
            size='count',
            sizes=(20, 200),
            alpha=0.8,
            palette='viridis'
        )

        # グラフのスタイル設定
        plt.title('Website Changes Timeline', fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('URL', fontsize=12)

        # x軸の日付フォーマット
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)

        # 凡例
        plt.legend(title='Number of Changes', bbox_to_anchor=(1.05, 1), loc='upper left')

        # グラフの保存
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

        logger.debug(f"Changes timeline saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error creating changes timeline: {e}")
        return False

def create_url_changes_chart(data, output_path):
    """
    URLごとの変更頻度グラフを作成する関数

    Args:
        data (pandas.DataFrame): 監視データのデータフレーム
        output_path (Path): 出力パス

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        if data.empty:
            logger.warning("No data available for visualization")
            return False

        # URLごとの変更回数を集計
        url_changes = data.groupby('url')['has_changed'].sum().reset_index()
        url_changes.columns = ['url', 'changes']
        url_changes = url_changes.sort_values('changes', ascending=False)

        # プロット
        plt.figure(figsize=(10, 6))
        sns.set(style="whitegrid")

        ax = sns.barplot(x='changes', y='url', data=url_changes, palette='viridis')

        # ラベルの設定
        plt.title('Number of Changes by URL', fontsize=16)
        plt.xlabel('Number of Changes', fontsize=12)
        plt.ylabel('URL', fontsize=12)

        # 値のラベル表示
        for i, v in enumerate(url_changes['changes']):
            ax.text(v + 0.1, i, str(v), va='center')

        # グラフの保存
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

        logger.debug(f"URL changes chart saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error creating URL changes chart: {e}")
        return False

def create_monitoring_report(report_dir, chart_type='all'):
    """
    監視レポートを作成する関数

    Args:
        report_dir (Path): レポートディレクトリのパス
        chart_type (str): 生成するグラフの種類 ('timeline', 'bar', 'all')

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        # 監視データの読み込み
        data = load_monitoring_data(days=30)

        if data.empty:
            logger.warning("No data available for report generation")
            return False

        from utils import get_timestamp
        timestamp = get_timestamp()

        if chart_type in ['timeline', 'all']:
            # タイムラインの作成
            timeline_path = report_dir / f"timeline_{timestamp}.png"
            create_changes_timeline(data, timeline_path)

        if chart_type in ['bar', 'all']:
            # URLごとの変更頻度グラフの作成
            bar_chart_path = report_dir / f"url_changes_{timestamp}.png"
            create_url_changes_chart(data, bar_chart_path)

        logger.info(f"Monitoring report created in {report_dir}")
        return True

    except Exception as e:
        logger.error(f"Error creating monitoring report: {e}")
        return False