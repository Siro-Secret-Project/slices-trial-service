import os
import boto3
from dotenv import load_dotenv
from urllib.parse import urlparse
from botocore.exceptions import ClientError


class AWSS3Client:
    """
    A client for interacting with AWS S3.

    This class provides methods to upload files to and download files from an S3 bucket.
    """

    def __init__(self, bucket_name: str = "slices-pdf-extraction", region_name: str = "ap-south-1") -> None:
        """
        Initializes the AWSS3Client with AWS credentials and default bucket name.

        Args:
            bucket_name (str, optional): The name of the S3 bucket. Defaults to "slices-pdf-extraction".

        Raises:
            ValueError: If AWS credentials or region are not set in environment variables.
        """
        load_dotenv()

        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = region_name

        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.region_name]):
            raise ValueError("AWS credentials or region are not set in environment variables.")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
        self.bucket_name = bucket_name

    def upload_file_to_s3(self, file_path: str, new_name: str) -> dict:
        """
        Uploads a file to the specified S3 bucket and returns the S3 URL.

        Args:
            file_path (str): The local path of the file to upload.
            new_name (str): The new name for the file in the S3 bucket.

        Returns:
            dict: A dictionary containing the success status, message, and S3 URL.
        """
        final_response = {
            "success": False,
            "message": "Failed to upload file to S3.",
            "data": None
        }
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, new_name)
            s3_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{new_name}"
            final_response.update({
                "success": True,
                "message": "File uploaded successfully.",
                "data": s3_url
            })
        except ClientError as e:
            error_message = f"An error occurred while uploading the file: {e}"
            print(error_message)
            final_response["message"] = error_message

        return final_response

    def download_file_from_s3(self, s3_url: str, local_path: str) -> dict:
        """
        Downloads a file from the specified S3 URL to a local path.

        Args:
            s3_url (str): The S3 URL of the file to download.
            local_path (str): The local path where the file will be saved.

        Returns:
            dict: A dictionary containing the success status and message.
        """
        final_response = {
            "success": False,
            "message": "Failed to download file from S3.",
            "data": None
        }
        try:
            # Parse the S3 URL to extract bucket name and object key
            parsed_url = urlparse(s3_url)
            bucket_name = parsed_url.netloc.split('.')[0]  # Extract bucket name from the URL
            object_key = parsed_url.path.lstrip('/')       # Extract object key (file name) from the URL

            # Download the file
            self.s3_client.download_file(bucket_name, object_key, local_path)
            final_response.update({
                "success": True,
                "message": f"File downloaded successfully to {local_path}.",
                "data": local_path
            })
        except Exception as e:
            error_message = f"An error occurred while downloading the file: {e}"
            print(error_message)
            final_response["message"] = error_message

        return final_response