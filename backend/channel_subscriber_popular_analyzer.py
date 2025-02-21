from db_utils import DBClient
from s3_utils import S3Client

class ChannelPopularityAnalyzer:
    """
    指定された動画のコメントを分析するクラス
    """

    def __init__(self, youtube_channel_id: str):
        """
        :param youtube_channel_id: 分析対象のチャンネルID
        """
        self.db = DBClient()
        self.s3 = S3Client()
        self.youtube_channel_id = youtube_channel_id

    # 分析に必要なもの
    # 視聴者人気のチャンネルのCSV from S3
    # 対象チャンネルデータのデモグラ
    # CSVのチャンネルデータとデモグラデータ、統計データ
    # 対象チャンネルおよびCSVの動画データ、統計データ

    def create_data(self):
        return {
            "target_channel_data": self.__a_channel_data(self.youtube_channel_id),
            "popular_channels_data": self.__channels_data()
        }

    def __get_popular_channel_data(self):
        """
        視聴者人気のチャンネルのCSVをS3から取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        s3_key = f"channel_subscriber_popular_channels/{self.youtube_channel_id}/{self.youtube_channel_id}.json"
        text = self.s3.load_json_as_text(s3_key)
        return text

    def extract_youtube_channel_id_from_json_data(self) -> list:
        """
        JSONデータからチャンネルIDを抽出
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        data = self.__get_popular_channel_data()
        return data["youtube_channel_id"]

    def __channels_data(self) -> list:
        """
        チャンネルデータを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        youtube_channel_ids = self.extract_youtube_channel_id_from_json_data()
        return [self.__a_channel_data(youtube_channel_id) for youtube_channel_id in youtube_channel_ids]

    # チャンネルデータ
    def __a_channel_data(self, youtube_channel_id: str):
        """
        チャンネルデータを取得
        """
        print(f"実行中のメソッド: {inspect.currentframe().f_code.co_name}")
        data = self.db.fetch_channel_data_by_youtube_channel_id(youtube_channel_id)
        age = self.__fetch_age_demogra(data["id"])
        gender = self.__fetch_gender_demogra(data["id"])
        return {
            "タイトル": data["title"],
            "説明": data["description"],
            "メタデータ": data["metadata"],
            "チャンネル開設日": data["published_at"],
            "年齢分布予測": age,
            "性別予測": gender
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
        data =  self.db.fetch_video_data(self.youtube_video_id)
        return {
            "タイトル": data["title"],
            "説明": data["description"],
            "メタデータ": data["metadata"],
            "投稿日": data["published_at"]
        }

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
