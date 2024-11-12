import logging
import json
import time
import random
import requests
from typing import Dict, Any, List
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions

from utility.decorators import retry_on_failure
from constants.xpaths import XPATHS

logger = logging.getLogger(__name__)


@retry_on_failure
def post_reviews(callback_url: str, reviews: List[Dict[str, Any]]):
    reviews_json = json.dumps(reviews)
    response = requests.post(callback_url, data=reviews_json)
    if response.status_code == 200:
        logger.info(f"Successfully posted reviews to {callback_url}")
    else:
        logger.error(
            f"Failed to post reviews to {callback_url} - Status Code: {response.status_code}"
        )
        response.raise_for_status()


@retry_on_failure
def navigate_to_url(driver, url: str):
    driver.get(url)


def extract_amazon_product_name(url: str) -> str:
    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split("/")
        if len(path_segments) >= 3:
            product_name = path_segments[1]
        else:
            product_name = None
        if product_name:
            product_name = unquote(product_name).replace("-", " ").title()
        return product_name if product_name else "Product name not found"
    except Exception as e:
        logger.error(f"Error extracting product name from Amazon URL: {url} - {e}")
        return "Product name not found"


def extract_flipkart_product_name(url: str) -> str:
    try:
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split("/")
        if len(path_segments) >= 1:
            product_name = path_segments[1]
        else:
            product_name = None
        if product_name:
            product_name = unquote(product_name).replace("-", " ").title()
        return product_name if product_name else "Product name not found"
    except Exception as e:
        logger.error(f"Error extracting product name from Flipkart URL: {url} - {e}")
        return "Product name not found"


def review_extractor(data: dict):
    url = data["url"]
    task_id = data["task_id"]
    callback_url = data.get("callback_url")
    platform = data["platform"]
    product_name = "Unknown product"
    reviews = []

    try:
        # Determine product name based on the platform
        if platform == "amazon":
            product_name = extract_amazon_product_name(url)
        elif platform == "flipkart":
            product_name = extract_flipkart_product_name(url)
        else:
            logger.error(f"Unknown platform: {platform} for URL: {url}")

        logger.info(f"Extracted product name: {product_name}")

        # Get XPath for reviews based on platform
        xpaths = XPATHS.get(platform)
        if not xpaths:
            raise ValueError(f"XPath configuration for platform {platform} not found.")

        # Set up Selenium WebDriver
        driver = webdriver.Chrome()
        current_url = url

        while current_url:
            logger.info(f"Navigating to URL: {current_url}")
            try:
                navigate_to_url(driver, current_url)

                # Wait until the reviews container is loaded
                wait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, xpaths["reviews_container"])
                    )
                )

                elements = driver.find_elements(By.XPATH, xpaths["reviews_container"])
                if not elements:
                    logger.warning(f"No reviews found for URL: {current_url}")

                for element in elements:
                    try:
                        rating = None
                        title = None
                        description = None
                        reviewer = None
                        reviewer_location = None

                        try:
                            rating = element.find_element(
                                By.XPATH, xpaths["rating"]
                            ).text.strip()
                        except selenium.common.exceptions.NoSuchElementException:
                            logger.warning(
                                f"Rating not found for review element at {current_url}"
                            )

                        try:
                            title = element.find_element(
                                By.XPATH, xpaths["title"]
                            ).text.strip()
                        except selenium.common.exceptions.NoSuchElementException:
                            logger.warning(
                                f"Title not found for review element at {current_url}"
                            )

                        try:
                            description = element.find_element(
                                By.XPATH, xpaths["description"]
                            ).text.strip()
                        except selenium.common.exceptions.NoSuchElementException:
                            logger.warning(
                                f"Description not found for review element at {current_url}"
                            )

                        try:
                            reviewer = element.find_element(
                                By.XPATH, xpaths["reviewer"]
                            ).text.strip()
                        except selenium.common.exceptions.NoSuchElementException:
                            logger.warning(
                                f"Reviewer not found for review element at {current_url}"
                            )

                        try:
                            reviewer_location = element.find_element(
                                By.XPATH, xpaths["reviewer_location"]
                            ).text.strip()
                        except selenium.common.exceptions.NoSuchElementException:
                            logger.warning(
                                f"Reviewer location not found for review element at {current_url}"
                            )
                        try:
                            posted_at = element.find_element(
                                By.XPATH, xpaths["posted_at"]
                            ).text.strip()
                        except selenium.common.exceptions.NoSuchElementException:
                            logger.warning(
                                f"Posted date not found for review element at {current_url}"
                            )

                        # Check if essential fields are missing
                        if not (
                            product_name
                            and platform
                            and rating
                            and title
                            and description
                            and reviewer
                        ):
                            raise ValueError(
                                f"Missing essential review information for URL: {current_url}"
                            )

                        # Append the review, with None for missing fields
                        reviews.append(
                            {
                                "token_id": task_id,
                                "product_name": product_name,
                                "site_name": platform,
                                "rating": rating,
                                "title": title,
                                "description": description,
                                "posted_at": posted_at,
                                "reviewer": reviewer,
                                "reviewer_details": {"location": reviewer_location},
                            }
                        )

                    except Exception as e:
                        logger.error(
                            f"Error processing review element for URL: {current_url} - {e}"
                        )
                        continue

                # Send extracted reviews to callback URL
                if reviews:
                    post_reviews(callback_url, reviews)

                # Random sleep to mimic human behavior and avoid detection
                time.sleep(random.randint(3, 7))

                # Check for the "Next" page
                try:
                    next_button = driver.find_element(By.XPATH, xpaths["pagination"])
                    next_page_url = next_button.get_attribute("href")
                    if next_page_url:
                        logger.info(f"Navigating to next page: {next_page_url}")
                        current_url = next_page_url
                    else:
                        logger.info("No more pages found. Ending review extraction.")
                        current_url = None

                except selenium.common.exceptions.NoSuchElementException:
                    logger.info("No 'Next' button found, ending pagination.")
                    current_url = None

            except selenium.common.exceptions.TimeoutException as te:
                logger.error(f"Timeout error while loading URL: {current_url} - {te}")
                try:
                    next_button = driver.find_element(By.XPATH, xpaths["pagination"])
                    next_page_url = next_button.get_attribute("href")
                    if next_page_url:
                        logger.info(
                            f"Timeout occurred, but 'Next' page exists. Moving to: {next_page_url}"
                        )
                        current_url = next_page_url
                    else:
                        logger.error("Timeout and no next page. Ending extraction.")
                        current_url = None
                except selenium.common.exceptions.NoSuchElementException:
                    logger.error("Timeout and no 'Next' button. Ending extraction.")
                    current_url = None

        driver.quit()
        # remove return add logs instead
        return {
            "status": "Reviews extracted successfully",
            "product_name": product_name,
            "reviews": reviews,
        }

    except ValueError as ve:
        logger.error(f"Platform or XPath error for URL: {url} - {ve}")
        return {"status": f"Error: {ve}", "product_name": product_name}

    except Exception as e:
        logger.error(
            f"Unexpected error during review extraction for URL: {url} - {e}",
            exc_info=True,
        )
        return {
            "status": "Internal server error",
            "error_message": str(e),
            "product_name": product_name,
        }
