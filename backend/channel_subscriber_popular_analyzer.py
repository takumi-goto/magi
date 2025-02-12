import pandas as pd
from datetime import datetime, timedelta
from db_utils import DBClient

class ChannelPopularityAnalyzer:
    """
    指定されたチャンネルの視聴者が他に登録しているチャンネルの傾向を分析するクラス
    """

    def __init__(self, channel_id: str, csv_path: str):
        """
        :param channel_id: 分析対象のチャンネルID
        :param csv_path: S3やローカルから取得したCSVのパス
        """
        self.channel_id = channel_id
        self.csv_path = csv_path
        self.db = DBClient()

        # CSVを読み込み
        self.df = pd.read_csv(self.csv_path)

    def get_related_channels(self):
        """
        指定された `channel_id` の行を取得し、関連チャンネル情報を取得。
        """
        df_filtered = self.df[self.df["チャンネルID"] == self.channel_id]

        if df_filtered.empty:
            return []

        # 関連チャンネルを取得（このCSVでは "channel_id" カラムに登録された他のチャンネルが格納）
        related_channels = df_filtered["チャンネルID"].unique().tolist()
        return related_channels

    def get_channel_metadata(self, channel_ids: list):
        """
        指定されたチャンネルIDの情報を Aurora から取得
        """
        return [self.db.fetch_channel_data(ch) for ch in channel_ids]

    def get_recent_videos(self, channel_ids: list):
        """
        指定されたチャンネルIDの直近30日以内の動画を取得
        """
        recent_date = datetime.now() - timedelta(days=30)
        videos = []

        sql = "SELECT * FROM videos WHERE channel_id = %s AND published_at >= %s"
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                for channel_id in channel_ids:
                    cur.execute(sql, (channel_id, recent_date))
                    videos.extend(cur.fetchall())
        finally:
            conn.close()
            self.db.close_tunnel()

        return videos

    def analyze_popular_channels(self):
        """
        - 指定されたチャンネルの視聴者が他に登録しているチャンネル一覧を取得
        - それらのチャンネルのメタデータを Aurora から取得
        - 直近30日間の動画情報を取得
        """
        related_channel_ids = self.get_related_channels()
        if not related_channel_ids:
            return {"message": "関連するチャンネルが見つかりません"}

        # Aurora からチャンネル情報取得
        channel_metadata = self.get_channel_metadata(related_channel_ids)

        # Aurora から直近30日間の動画情報取得
        recent_videos = self.get_recent_videos(related_channel_ids)

        return {
            "target_channel": self.channel_id,
            "related_channels": related_channel_ids,
            "channel_metadata": channel_metadata,
            "recent_videos": recent_videos
        }
