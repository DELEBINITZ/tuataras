import logging
from logic.review_extractor import review_extractor
from celery.exceptions import Reject

from config.env_config import sttgs

logger = logging.getLogger(__name__)

from celery import Celery

celery_app = Celery(
    "tasks",
    broker=sttgs.get("CELERY_BROKER_URL"),
    backend=sttgs.get("CELERY_BAKCEND_URI"),
)


"""Celery task to extract reviews from a given URL and process them."""
@celery_app.task(bind=True, track_started=True)
def extract_reviews_from_page(self, data: dict):
    try:
        logger.info("Starting review extraction task.")

        # Update task state to indicate initial progress
        self.update_state(state="PROGRESS")

        # Check and validate required fields in data
        required_fields = ["url", "callback_url", "platform"]
        for field in required_fields:
            if not data.get(field):
                error_message = f"Missing required field: {field}"
                logger.error(error_message)
                self.update_state(state="FAILURE", meta={"error": error_message})
                raise Reject(error_message)

        # Check for task ID and assign it if necessary
        data["task_id"] = self.request.id

        platform = data["platform"].lower()
        logger.info(
            f"Extracting reviews for URL: {data['url']} on platform: {platform}"
        )

        # Perform the review extraction
        review_extractor(data)

        # Update task state to success upon completion
        self.update_state(
            state="SUCCESS", meta={"result": "Reviews extracted successfully"}
        )
        logger.info("Review extraction completed successfully.")

    except ValueError as e:
        error_message = f"Value error: {str(e)}"
        logger.error(error_message)
        self.update_state(state="FAILURE", meta={"error": error_message})
        raise Reject(error_message)
    except Exception as e:
        error_message = f"General error: {str(e)}"
        logger.error(error_message, exc_info=True)
        self.update_state(state="FAILURE", meta={"error": error_message})
        raise Reject(error_message)
