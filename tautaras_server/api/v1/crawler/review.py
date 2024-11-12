from fastapi import APIRouter, HTTPException, Request
from typing import Any, Dict
import json
from celery.result import AsyncResult
from celery.exceptions import CeleryError
from datetime import datetime
import hashlib
import logging

from core.infra.celery.celery_app import celery_app
from core.models.dto.crawler.reviews import ExtractReviewRequest
from core.utility.crypto import get_hash
from core.infra.cache.cache_manager import Cache
from core.infra.elasticstack.elastic import create_document, document_exists
from api.utility.review_utility import identify_platform, is_safe_url

reviews_router = APIRouter()

logger = logging.getLogger(__name__)


@reviews_router.post("/extract")
async def extract_reviews(request: ExtractReviewRequest) -> Dict[str, Any]:
    response: Dict[str, Any] = {}

    try:
        url = request.url
        logger.info(f"Received request to extract reviews from URL: {url}")
        is_safe = is_safe_url(url)
        if not is_safe:
            response["success"] = False
            response["message"] = "URL is not safe"
            return response

        # check if the URL is valid
        platform = identify_platform(url)
        logger.info(f"Platform identified as '{platform}' for URL: {url}")

        encoded_url = get_hash(url)
        logger.debug(f"Encoded URL hash generated: {encoded_url}")

        # Check if the job is already present
        task_id = await Cache.backend.get(f"task_status::{encoded_url}")
        if task_id:
            job_status = await get_job_status(task_id)
            logger.info(
                f"Found existing task ID: {task_id} with status: {job_status.get('status')}"
            )

            if job_status.get("status") in ("PROGRESS", "STARTED"):
                response["message"] = "Job is already present."
                return response
            else:
                logger.info(
                    f"Job with task ID {task_id} is not present. Proceeding to submit a new job."
                )

        # data for message queue
        data = {
            "url": url,
            "callback_url": "http://0.0.0.0/api/v1/reviews/ingest",
            "platform": platform,
        }

        logger.debug(f"Data prepared for task: {data}")

        # Submit a new extraction job
        res = celery_app.send_task(
            "tasks.extract_reviews_from_page",
            kwargs={"data": data},  # Pass the data as a dictionary
        )
        task_id = res.task_id
        logger.info(f"Task submitted to Celery with ID: {task_id}")

        # Cache the task ID
        await Cache.backend.set(f"task_status::{encoded_url}", task_id, 60 * 60)
        logger.info(f"Task ID cached with key 'task_status::{encoded_url}' for 1 hour")

        # Success response
        response["success"] = True
        response["message"] = "Job has been submitted successfully."
        response["job_id"] = task_id

    except ValueError as e:
        logger.error(f"ValueError encountered: {e}")
        response["success"] = False
        response["status"] = str(e)
        raise HTTPException(status_code=400, detail=response)

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
        response["success"] = False
        response["message"] = "Internal server error"
        response["error_message"] = str(e)
        raise HTTPException(status_code=500, detail=response)

    logger.info("Extract reviews request processed successfully")
    return response


@reviews_router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    response: Dict[str, Any] = {}
    try:
        # Get the job status
        result = AsyncResult(job_id)
        print(f"Job ID: {job_id}, Status: {result.state}")

        response["status"] = result.state
        response["progress"] = result.info.get("progress") if result.info else "unknown"

    except (CeleryError, Exception) as e:
        print(f"Error getting job status for ID: {job_id} - {e}")
        response["status"] = "error"
        response["error_message"] = str(e)

    return response


@reviews_router.post("/ingest")
async def ingest_reviews(request: Request):
    try:
        reviews_data = await request.json()

        for review in reviews_data:
            review_hash_input = (
                review["title"]
                + review["description"]
                + str(review["rating"])
                + review["reviewer"]
                + review["reviewer_details"].get("location", "")
                + review["product_name"]
                + review["site_name"]
            )

            review_id = hashlib.sha256(review_hash_input.encode()).hexdigest()

            # Assign indexed and updated timestamps
            timestamp = datetime.now().isoformat()
            review["review_id"] = review_id
            review["indexed_at"] = timestamp
            review["updated_at"] = timestamp
            # TODO: add date parser here and add date in database utc format
            review["published_at"] = "add here"

            # Check if the review already exists
            exists = await document_exists("reviews", review_id)
            if exists:
                logger.info(
                    f"Review with ID '{review_id}' already exists. Skipping insertion."
                )
                continue

            # Insert the review into Elasticsearch if it doesn't exist
            _, error = await create_document("reviews", review_id, review)
            if error:
                logger.error(f"Error inserting review with ID '{review_id}': {error}")
                continue
            logger.info(f"Review with ID '{review_id}' successfully ingested.")

        return {"status": "Success", "message": "Reviews ingested successfully"}

    except Exception as e:
        logger.error(f"Error ingesting reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))