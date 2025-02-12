import os
import pymysql
import paramiko
from sshtunnel import SSHTunnelForwarder

class DBClient:
    """
    Aurora MySQL への接続クライアント（SSHポートフォワーディングを使用）。
    """

    def __init__(self):
        # 環境変数から必要な情報を取得
        self.ssh_host = os.getenv("SSH_HOST")  # 例: "eviry-jump1.eviry.com"
        self.ssh_port = int(os.getenv("SSH_PORT", "22"))
        self.ssh_user = os.getenv("SSH_USER")
        self.ssh_key_path = os.getenv("SSH_KEY_PATH")  # 例: "~/.ssh/id_rsa"
        self.remote_host = os.getenv("REMOTE_HOST")    # 例: "db-master.kamuitracker.com"
        self.remote_port = int(os.getenv("REMOTE_PORT", "3306"))
        self.local_host = os.getenv("LOCAL_HOST", "127.0.0.1")
        self.local_port = int(os.getenv("LOCAL_PORT", "3307"))

        # DB接続情報
        self.db_user = os.getenv("DB_USER", "root")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", "my_database")

        self.server = None  # SSHTunnelForwarder インスタンス

    # ========== 以下は実際のDB操作例 ==========
    def fetch_channel_id_by(self, youtube_video_id: str) -> str:
        """
        指定された動画IDからチャンネルIDを取得
        """
        sql = "SELECT channel_id FROM videos WHERE youtube_video_id = %s LIMIT 1"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (youtube_video_id,))
                row = cur.fetchone()
                return row["channel_id"] if row else None
        finally:
            conn.close()
            self.__close_tunnel()

    def fetch_channel_data_by_id(self, channel_id: str):
        """
        チャンネルID からチャンネル情報を取得する例
        """
        sql = "SELECT youtube_channel_id, title, description, published_at, branding_keywords, metadata FROM channels WHERE id = %s"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (channel_id,))
                row = cur.fetchone()
                return row
        finally:
            conn.close()
            self.__close_tunnel()

    def fetch_channel_data_by_youtube_channel_id(self, channel_id: str):
        """
        youtube_チャンネルID からチャンネル情報を取得する例
        """
        sql = "SELECT youtube_channel_id, title, description, published_at, branding_keywords, metadata FROM channels WHERE youtube_channel_id = %s"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (channel_id,))
                row = cur.fetchone()
                return row
        finally:
            conn.close()
            self.__close_tunnel()

    def fetch_video_data(self, youtube_video_id: str):
        """
        指定された動画IDから動画データを取得
        """
        sql = "SELECT youtube_video_id, title, title_keywords, description, metadata, published_at FROM videos WHERE youtube_video_id = %s"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (youtube_video_id,))
                row = cur.fetchone()
                return row
        finally:
            conn.close()
            self.__close_tunnel()

    def fetch_age_demogra_data(self, channel_id: str):
        """
        指定された動画IDからデモグラフィックデータを取得
        """
        sql = "SELECT * FROM channel_age_predictions WHERE channel_id = %s"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (channel_id,))
                row = cur.fetchone()
                return row
        finally:
            conn.close()
            self.__close_tunnel()

    def fetch_gender_demogra_data(self, channel_id: str):
        """
        指定された動画IDからデモグラフィックデータを取得
        """
        sql = "SELECT * FROM channel_gender_predictions WHERE channel_id = %s"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (channel_id,))
                row = cur.fetchone()
                return row
        finally:
            conn.close()
            self.__close_tunnel()

    def fetch_video_stats(self, youtube_video_id: str, days: int = 5):
        video_id = self.__fetch_video_id(youtube_video_id)
        sql = "SELECT * FROM video_statistics WHERE video_id = %s AND update_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) ORDER BY update_date DESC"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (video_id, days))
                row = cur.fetchone()
                return row
        finally:
            conn.close()
            self.__close_tunnel()

    # private
    def __setup_port_forwarding(self):
        """
        SSHポートフォワーディングをセットアップし、SSHTunnelForwarderを返す。
        """
        pkey = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)

        server = SSHTunnelForwarder(
            (self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_user,
            ssh_pkey=pkey,
            remote_bind_address=(self.remote_host, self.remote_port),
            local_bind_address=(self.local_host, self.local_port)
        )
        return server

    def __get_connection(self):
        """
        SSHトンネルを開始し、ローカルポート経由で Aurora MySQL に接続する。
        """
        if not self.server:
            self.server = self.__setup_port_forwarding()

        # トンネル開始
        self.server.start()
        print(f"SSHトンネル開始: local={self.local_host}:{self.local_port} -> remote={self.remote_host}:{self.remote_port}")

        # self.local_host / self.local_port を使って MySQL に接続
        conn = pymysql.connect(
            host=self.local_host,
            port=self.local_port,
            user=self.db_user,
            password=self.db_password,
            db=self.db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn

    def __close_tunnel(self):
        """
        SSHトンネルを停止する。
        """
        if self.server:
            self.server.stop()
            print("SSHトンネルを停止しました")
            self.server = None


    def __fetch_video_id(self, youtube_video_id: str) -> str:
        """
        指定された動画IDからyotuube_video_idを取得
        """
        sql = "SELECT id FROM videos WHERE youtube_video_id = %s LIMIT 1"
        conn = self.__get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (youtube_video_id,))
                row = cur.fetchone()
                return row["id"] if row else None
        finally:
            conn.close()
            self.__close_tunnel()
