import pandas as pd
from datetime import datetime, timedelta
from db_utils import DBClient
from s3_utils import S3Client
import inspect

class CommentAnalyzer:
    """
    指定された動画のコメントを分析するクラス
    """

    def __init__(self, youtube_video_id: str):
        """
        :param video_id: 分析対象のチャンネルID
        """
        self.db = DBClient()
        self.s3 = S3Client()
        self.youtube_video_id = youtube_video_id
        self.channel_id = self.db.fetch_channel_id_by(self.youtube_video_id)
        self.youtube_channel_id = self.__get_youtube_channel_id_by(self.channel_id)


    # 分析に必要なもの
    # デモグラ（推定データ）
    # コメントデータ
    # 動画データ
    # チャンネルデータ
    # 動画の統計データ

    def create_data(self):
        video_data = self.__fetch_video_data()
        basic_data = {
            "comment_data": self.__fetch_comment_data(video_data["youtube_video_id"]),
            "channel_data": self.__a_channel_data(self.youtube_channel_id),
            "age_prediction": self.__fetch_age_demogra(),
            "gender_prediction": self.__fetch_gender_demogra(),
            "video_data": {
                "タイトル": video_data["title"],
                "説明": video_data["description"],
                "メタデータ": video_data["metadata"],
                "投稿日": video_data["published_at"]
            },
            "video_stats": self.__fetch_video_stats(10)
        }
        if video_data["is_sponsored"] == 1:
            other_sponsored_video_data = self.db.fetch_other_product_videos(str(video_data['product_id']))

            if other_sponsored_video_data:
                basic_data["other_sponsored_video_data"] = []

                for video in other_sponsored_video_data:
                    print("other_sponsored_video_data", video)
                    basic_data["other_sponsored_video_data"].append({
                        "タイトル": video["title"],
                        "説明": video["description"],
                        "メタデータ": video["metadata"],
                        "投稿日": video["published_at"]
                    })
                    comment_data = self.__fetch_comment_data(video["youtube_video_id"])
                    basic_data["other_sponsored_video_comments"].append(comment_data) if comment_data else None

        return basic_data

    # youtube_channel_idを取得
    def __get_youtube_channel_id_by(self, channel_id: str) -> str:
        """
        指定された動画IDからチャンネルIDを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        youtube_channel_id = self.db.fetch_channel_data_by_id(channel_id)["youtube_channel_id"]
        return youtube_channel_id

    # コメントデータ
    def __fetch_comment_data(self, youtube_video_id):
        """
        コメントCSVをS3から取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        channel_id = self.db.fetch_channel_id_by(youtube_video_id)
        youtube_channel_id = self.__get_youtube_channel_id_by(channel_id)
        s3_key = f"video_comments/{youtube_channel_id}/{youtube_video_id}.csv"
        csv_text = self.s3.load_csv_as_text(s3_key)
        return csv_text

    # チャンネルデータ
    def __a_channel_data(self, youtube_channel_id: str):
        """
        チャンネルデータを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        data = self.db.fetch_channel_data_by_youtube_channel_id(youtube_channel_id)
        return {
            "タイトル": data["title"],
            "説明": data["description"],
            "メタデータ": data["metadata"],
            "チャンネル開設日": data["published_at"]
        }

    # デモグラデータ
    def __fetch_age_demogra(self):
        """
        デモグラデータを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        ages = self.db.fetch_age_demogra_data(self.channel_id)
        return {
            "13〜17歳": f"{ages["prediction_age_13_17"] * 100}%",
            "18~24歳": f"{ages["prediction_age_18_24"] * 100}%",
            "25~34歳": f"{ages["prediction_age_25_34"] * 100}%",
            "35-44歳": f"{ages["prediction_age_35_44"] * 100}%",
            "45-54歳": f"{ages["prediction_age_45_54"] * 100}%",
            "55-64歳": f"{ages["prediction_age_55_64"] * 100}%",
            "65歳以上": f"{ages["prediction_age_65_"] * 100}%"
        }

    def __fetch_gender_demogra(self):
        """
        デモグラデータを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        genders = self.db.fetch_gender_demogra_data(self.channel_id)
        return {
            "推定男性比": f"({(100 - genders["prediction_rate"])}%",
            "推定女性比": f"{genders["prediction_rate"]}%"
        }

    # 動画データ
    def __fetch_video_data(self):
        """
        動画データを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        return self.db.fetch_video_data(self.youtube_video_id)

    # 動画の統計データ
    def __fetch_video_stats(self, days):
        """
        動画の統計データを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        stats = self.db.fetch_video_stats(self.youtube_video_id, days)
        return {
            "視聴回数": stats["view_count"],
            "いいね数": stats["like_count"],
            "コメント数": stats["comment_count"]
        }
