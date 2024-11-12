from fastapi import APIRouter, HTTPException, Request, Query
from typing import Any, Dict
import json
from celery.result import AsyncResult
from celery.exceptions import CeleryError
from datetime import datetime
import hashlib
import logging
import dateparser
from typing import Optional

from core.models.dto.crawler.reviews import ReviewDTO, PaginatedResponse
from core.infra.celery.celery_app import celery_app
from core.models.dto.crawler.reviews import ExtractReviewRequest, JobStatusResponse
from core.utility.crypto import get_hash
from core.utility.validation import validate_str_params, validate_token_id
from core.infra.cache.cache_manager import Cache
from api.utility.review_utility import identify_platform, is_safe_url
from core.infra.elasticstack.elastic import (
    create_document,
    document_exists,
    search_documents,
)

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
            "callback_url": "http://0.0.0.0:80/api/v1/reviews/ingest",
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


@reviews_router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    response = JobStatusResponse(status="unknown")  

    try:
        # Get the job status
        result = AsyncResult(job_id)
        print(f"Job ID: {job_id}, Status: {result.state}")

        response.status = result.state
        response.progress = result.info.get("progress") if result.info else "unknown"

    except (CeleryError, Exception) as e:
        print(f"Error getting job status for ID: {job_id} - {e}")
        response.status = "error"
        response.error_message = str(e)

    return response


@reviews_router.post("/ingest")
async def ingest_reviews(request: Request):
    try:
        reviews_data = await request.json()

        for review in reviews_data:
            review_hash_input = (
                str(review.get("title", ""))
                + str(review.get("description", ""))
                + str(review.get("rating", ""))
                + str(review.get("reviewer", ""))
                + str(review.get("reviewer_details", {}).get("location", ""))
                + str(review.get("product_name", ""))
                + str(review.get("site_name", ""))
            )

            # review_id is a hash of the review data to ensure uniqueness and avoid duplicates
            review_id = hashlib.sha256(review_hash_input.encode()).hexdigest()

            timestamp = datetime.now().isoformat()
            review["review_id"] = review_id
            review["indexed_at"] = timestamp
            review["updated_at"] = timestamp
            posted_at = dateparser.parse(
                review.get("posted_at"),
                settings={"TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": True},
            )
            review["posted_at"] = posted_at

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


@reviews_router.get("")
async def get_reviews(
    product_name: Optional[str] = Query(None),
    site_name: Optional[str] = Query(None),
    rating: Optional[str] = Query(None),
    reviewer: Optional[str] = Query(None),
    token_id: Optional[str] = Query(None),
    page: int = Query(1, description="Page number"),
    size: int = Query(10, description="Number of results per page"),
):
    try:
        from_ = (page - 1) * size

        query = {"query": {"bool": {"must": []}}}

        if token_id:
            validate_token_id(token_id)
            query["query"]["bool"]["must"].append({"match": {"token_id": token_id}})
        if site_name:
            validate_str_params(product_name)
            query["query"]["bool"]["must"].append({"match": {"site_name": site_name}})
        if rating:
            if not isinstance(rating, (int, float)):
                raise ValueError("Invalid rating format")
            query["query"]["bool"]["must"].append({"match": {"rating": rating}})
        if reviewer:
            validate_str_params(reviewer)
            query["query"]["bool"]["must"].append({"match": {"reviewer": reviewer}})
        if product_name:
            validate_str_params(product_name)
            query["query"]["bool"]["must"].append(
                {
                    "match": {
                        "product_name": {"query": product_name, "fuzziness": "AUTO"}
                    }
                }
            )

        results, total_hits = await search_documents(
            "reviews", query, from_=from_, size=size
        )

        if results is None:
            raise HTTPException(status_code=500, detail="Error retrieving reviews")

        formatted_results = [
            ReviewDTO(
                review_id=result["_source"]["review_id"],
                product_name=result["_source"]["product_name"],
                site_name=result["_source"]["site_name"],
                rating=result["_source"]["rating"],
                title=result["_source"]["title"],
                description=result["_source"]["description"],
                reviewer=result["_source"]["reviewer"],
                reviewer_location=result["_source"]
                .get("reviewer_details", {})
                .get("location"),
                indexed_at=result["_source"]["indexed_at"],
                updated_at=result["_source"]["updated_at"],
            )
            for result in results
        ]

        response = PaginatedResponse(
            status="Success",
            page=page,
            page_size=size,
            total_results=total_hits,
            total_pages=(total_hits + size - 1) // size,
            reviews=formatted_results,
        )

        return response.dict()

    except Exception as e:
        logger.error(f"Error retrieving reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))
