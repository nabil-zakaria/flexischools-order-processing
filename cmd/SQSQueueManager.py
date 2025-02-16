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

    def _receive_messages(self) -> list:
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

    def _delete_message(self, message: dict) -> None:
        """Delete a message of the SQS eueu

        Args:
            message (dict): The message to be deleted
        """
        self.sqs.delete_message(
            QueueUrl=self.sqs_queue_url, ReceiptHandle=message["ReceiptHandle"]
        )
        logger.info("Message deleted")

    def _process_messages(self, messages: list) -> None:
        """Processes the list of messages taken from the SQS queue

        Args:
            messages (list): The messages to be processed
        """
        for message in messages:
            logger.info(f"Processing message: {message['Body']}")
            # TODO: Process and write the message to the RDS DB
            # Then delete the message
            self._delete_message(message=message)

    def process_queue(self) -> None:
        """Long polls the SQS queue and processes the messages"""
        while True:
            try:
                messages = self._receive_messages()
                self._process_messages(messages=messages)
            except Exception as e:
                logger.exception(
                    f"Error occured processing messages on queue: {(repr(e))}"
                )
                time.sleep(5)  # Wait 5 sec before retrying
