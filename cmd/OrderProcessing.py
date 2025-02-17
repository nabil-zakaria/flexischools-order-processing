import os
import logging
import time
from flask import Flask
from threading import Thread
from SQSQueueManager import SQS
from SecretsManager import Secrets
from RDSManager import RDS

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel(logging.INFO)

# Flask app for health check
app = Flask(__name__)


@app.route("/health")
def health_check():
    return "OK", 200  # ALB expects 200 status for a healthy target


def process_queue(sqs: SQS, rds: RDS) -> None:
    """Long polls the SQS queue and processes the messages"""

    while True:
        try:
            messages = sqs.receive_messages()
            for message in messages:
                order_details = message["Body"]
                logger.info(f"Processing message: {order_details}")
                rds.write_to_table(
                    table_name=os.environ["DB_TABLE_NAME"],
                    column_name="order_details",
                    value=order_details,
                )
                sqs.delete_message(message=message)
        except Exception as e:
            logger.exception(f"Error occured processing messages on queue: {(repr(e))}")
            time.sleep(5)  # Wait 5 sec before retrying


if __name__ == "__main__":
    logger.info("Starting health check server...")
    Thread(target=lambda: app.run(host="0.0.0.0", port=80), daemon=True).start()

    logger.info("Retrieving database credentials from Secrets Manager")
    secret = Secrets().get_secret(secret_name=os.environ["SECRET_ARN"])

    logger.info("Connecting to RDS Database")
    db_config = {
        "db_host": os.environ["DB_HOST"],
        "db_name": os.environ["DB_NAME"],
        "db_user": os.environ["DB_USER"],
        "db_port": os.environ["DB_PORT"],
        "db_password": secret["password"],
    }
    rds = RDS(db_config=db_config)
    if rds.confirm_table_exists(table_name=os.environ["DB_TABLE_NAME"]) is False:
        rds.create_table(table_name=os.environ["DB_TABLE_NAME"])

    logger.info("Sarting SQS Poller...")
    sqs = SQS(queue_url=os.environ["QUEUE_URL"])
    process_queue(sqs=sqs, rds=rds)
