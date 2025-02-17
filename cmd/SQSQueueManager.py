import boto3
import time
import logging

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel(logging.INFO)


class SQS:
    def __init__(self, queue_url: str):
        self.sqs = boto3.client("sqs")
        self.sqs_queue_url = queue_url

    def receive_messages(self) -> list:
        """Long polls the SQS queue, pulling messages off one at a time.

        Returns:
            list: The list of SQS Messages
        """
        response = self.sqs.receive_message(
            QueueUrl=self.sqs_queue_url,
            AttributeNames=["All"],
            MaxNumberOfMessages=1,
            MessageAttributeNames=["All"],
            WaitTimeSeconds=20,  # Long polling for up to 20 seconds
        )
        messages = response.get("Messages", [])
        return messages

    def delete_message(self, message: dict) -> None:
        """Delete a message of the SQS eueu

        Args:
            message (dict): The message to be deleted
        """
        self.sqs.delete_message(
            QueueUrl=self.sqs_queue_url, ReceiptHandle=message["ReceiptHandle"]
        )
        logger.info("Message deleted")
