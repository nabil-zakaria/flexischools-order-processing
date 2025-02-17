import boto3
import logging
import json

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel(logging.INFO)


class Secrets:
    def __init__(self):
        self.secret = boto3.client("secretsmanager")

    def get_secret(self, secret_name: str) -> dict:
        """Retrieves the secret with secret_name from AWS Secrets Manager

        Args:
            secret_name (str): Name of secret to retrieve

        Returns:
            dict: Object containing username and password
        """
        response = self.secret.get_secret_value(SecretId=secret_name)
        secret = response["SecretString"]
        return json.loads(secret)
