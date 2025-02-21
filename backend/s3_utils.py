import os
import boto3
from dotenv import load_dotenv

load_dotenv()  # .env からAWSキーを読み込み
from io import BytesIO

class S3Client:
    def __init__(self, default_bucket: str = "kt-production"):
        """
        バケット名などを .env から読み取り、boto3 クライアント初期化
        """
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", default_bucket)

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )

    def load_csv_as_text(self, s3_key: str) -> str:
        """
        S3上の CSV (テキスト) をダウンロードして、文字列として返す
        """
        buffer = BytesIO()
        self.s3_client.download_fileobj(
            Bucket=self.bucket_name,
            Key=s3_key,
            Fileobj=buffer
        )
        buffer.seek(0)
        csv_text = buffer.read().decode("utf-8")
        return csv_text

    def load_json_as_text(self, s3_key: str) -> str:
        """
        S3上の JSON (テキスト) をダウンロードして、文字列として返す
        """
        buffer = BytesIO()
        self.s3_client.download_fileobj(
            Bucket=self.bucket_name,
            Key=s3_key,
            Fileobj=buffer
        )
        buffer.seek(0)
        json_text = buffer.read().decode("utf-8")
        return json_text

    def load_file_to_local(self, s3_key: str, local_path: str):
        """
        S3のファイルをローカルに保存する（CSV以外でも可）
        """
        self.s3_client.download_file(
            Bucket=self.bucket_name,
            Key=s3_key,
            Filename=local_path
        )
        return local_path
