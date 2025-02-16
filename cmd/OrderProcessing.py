import os
import logging
from flask import Flask
from threading import Thread
from SQSQueueManager import SQS

logger = logging.getLogger()
logging.basicConfig()
logger.setLevel(logging.INFO)

# Flask app for health check
app = Flask(__name__)


@app.route("/health")
def health_check():
    return "OK", 200  # ALB expects 200 status for a healthy target


if __name__ == "__main__":
    logger.info("Starting health check server...")
    Thread(target=lambda: app.run(host="0.0.0.0", port=80), daemon=True).start()

    logger.info("Sarting SQS Poller...")
    sqs = SQS(queue_url=os.environ["QUEUE_URL"])
    sqs.process_queue()
