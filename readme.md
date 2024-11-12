
## Problem Statement

Develop an API server that can extract reviews from specified Amazon or Flipkart product page. The API should automatically detect the site based on the URL, 
and scrape the reviews, manage pagination to collect all available reviews, and return the data in a structured JSON format.
API service should be capable of handling thousands of requests per day.

# Tautaras - Review Extraction Server

**Tautaras** is a backend service built with **FastAPI** for extracting and managing reviews from Flipkart product pages. Designed for high efficiency, the server integrates with **RabbitMQ**, **Celery**, **Redis**, and **Elasticsearch** to support asynchronous task processing, progress tracking, and structured data storage.

## Features
- Accepts a product URL and generates a unique job ID for tracking.
- Asynchronously extracts reviews using Celery workers and RabbitMQ message queuing.
- Stores extracted reviews in Elasticsearch for structured and efficient data retrieval.
- Provides task status tracking with Redis and an API endpoint to query job progress.


## Architecture

![Logo](https://d2rstorage2.blob.core.windows.net/widget/November/12/664cc278-650a-4b39-8542-5b55584cd6ae/1731445060765.webp)

The FastAPI server exposes endpoint for submitting tasks to extract reviews from product pages. It uses Celery as a task queue to manage the background extraction of reviews, Redis for caching task status, and includes security checks to ensure URLs are safe.

Whenever user submits a job the system checks if there is already an ongoing task for the same URL to prevent duplicate jobs.It does this by generating a unique identifier for the URL and checking if an entry for it already exists in the cache (Redis).If a task is found and is still in progress, the API returns a response indicating that the job is already present.

If no duplicate task exists, the API prepares relevant data, including the URL and platform details.
This data is sent as a new task to a background task queue (Celery), which will handle the review extraction process.Once the task is submitted, a unique identifier for it is stored in the cache.
This enables the system to track and retrieve the status of the task, ensuring quick responses to future status queries without duplicating work.

The callback_url in the extract_reviews API serves as a destination for the extracted review data once processing is complete, it represents the endpoint where the extracted review data will be sent once processing is finished. Instead of waiting for data extraction in real-time, which could block the API, the system asynchronously processes the task and, upon completion, sends the results back to this designated endpoint (callback URL). This approach is effective for applications that require data ingestion without direct user intervention, allowing for seamless, automated workflows.

The API submits the task, including the callback_url, to a message queue ie RabbitMQ. This task includes:
- url for the product page to be scraped.
- platform indicating the source (e.g., Amazon, Shopify).
- callback_url where the extracted data will be sent after completion.

A Celery worker retrieves the task from RabbitMQ, receives the URL, platform, and callback_url, and begins extracting reviews based on the given data.The worker processes this task independently of the API server, avoiding any real-time blocking. Once data extraction is complete, the Celery worker sends a POST request to the callback_url, effectively delivering the processed review data.
```
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
```

This data is then store to Elasticsearch




### Prerequisite
If docker is not already installed, download and install it from [Docker](https://docs.docker.com/get-started/get-docker/).
Run the following commands to pull the official Docker images for Redis, RabbitMQ and start each service in a Docker container.
- `docker run -d --name redis-container -p 6379:6379 redis:latest`
- `docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:4.0-management`
Use the [link](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) to install Elasticsearch with docker.



Run the following cmd
`git clone https://github.com/DELEBINITZ/tuataras.git` to make a local copy of a remote Git repository.

`cd tuataras` move to the folder where repository is cloned

create a venv for both tautaras_server and tautaras_worker in different terminals by using following commands
- `python3 -m venv .server_venv`
- `python3 -m venv .worker_venv`
This is important if tautaras_server and tautaras_worker require different versions of the same library or have unique dependencies.

After setting up the environments with the specified commands, you can activate each in different terminals:

- `source .server_venv/bin/activate`
- `source .worker_venv/bin/activate`

run below command in each termianl to install all the packages and dependencies listed in a file called requirements.txt. 
- `pip install -r requirements.txt`

Once you RabbitMQ, Redis and Elasticsearch are up and running
add their credentials in the env files use the env variable from .env.example file.

To start the Fastapi server run the following command

- `python main.py --port 80 --auto-reload-server`

To start the celery worker run the following command
- `celery -A tasks worker --loglevel=DEBUG`


# REST API

The REST API to the Fastapi is described below.

## Submit review extraction job

### Request

`POST /api/v1/reviews/extract`

    curl --location 'http://0.0.0.0:80/api/v1/reviews/extract' \
    --header 'Accept: */*' \
    --header 'Accept-Language: en-GB,en-US;q=0.9,en;q=0.8' \
    --header 'Connection: keep-alive' \
    --header 'Content-Type: application/json' \
    --data '{
    "url":"https://www.flipkart.com/apple-iphone-16-teal-128-gb/product-reviews/itmce4bb3f55cc2f?pid=MOBH4DQFSY9ETDUU&lid=LSTMOBH4DQFSY9ETDUU6JV9DJ&marketplace=FLIPKART"
    }'

### Response

    {
        "success": true,
        "message": "Job has been submitted successfully.",
        "job_id": "75158f32-3957-40f6-812b-b7ce563ad4a7"
    }

## Get the status of the job

### Request

`GET /api/v1/reviews/status/b8c769af-f704-4586-aed8-7ca73d141237`

    curl --location 'http://0.0.0.0:80/api/v1/reviews/status/b8c769af-f704-4586-aed8-7ca73d141237' \
    --header 'Content-Type: application/json'

### Response

    HTTP/1.1 201 Created
    Date: Thu, 24 Feb 2011 12:36:30 GMT
    Status: 201 Created
    Connection: close
    Content-Type: application/json
    Location: /thing/1
    Content-Length: 36

    {"id":1,"name":"Foo","status":"new"}

## Get a specific Thing

### Request

`GET /thing/id`

    curl -i -H 'Accept: application/json' http://localhost:7000/thing/1

### Response

    {
        "status": "SUCCESS",
        "progress": null
    }

## Get the reviews

### Request

`GET api/v1/reviews?query_params`

    curl --location 'http://0.0.0.0:80/api/v1/reviews?token_id=8ecc7823-42f3-40c6-819a-a6664e33effe&page=1&rating=4&    product_name=iphone' \
    --header 'Content-Type: application/json' \
    --header 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.      115 Safari/537.36' \
    --header 'Accept-Encoding: gzip'

### Response

    {
    "status": "Success",
    "page": 1,
    "page_size": 10,
    "total_results": 147,
    "total_pages": 15,
    "reviews": 
        [
        {
            "review_id": "2dfbf31939398d5c8761288ec3543e10fe4d46c215b9ff6ed897c01286587bd4",
            "product_name": "Lg 7 Kg 5 Star Wind Jet Dry Collar Scrubber Rust Free Plastic Base Semi Automatic Top Load Washing Machine Grey White",
            "site_name": "flipkart",
            "rating": 4.0,
            "title": "Really Nice",
            "description": "Good washing machine ☺️",
            "reviewer": "shivam kumar",
            "reviewer_location": ", Kiratpur",
            "indexed_at": "2024-11-11T19:23:09.207675",
            "updated_at": "2024-11-11T19:23:09.207675"
        },
        {
            "review_id": "b2fed0036b8cc1fb91a23a1cc4921062889333dbce9f91317456ec1e43a27ca5",
            "product_name": "Lg 7 Kg 5 Star Wind Jet Dry Collar Scrubber Rust Free Plastic Base Semi Automatic Top Load Washing Machine Grey White",
            "site_name": "flipkart",
            "rating": 5.0,
            "title": "Just wow!",
            "description": "This product is very good and performance is excellent is am so happy to purchase washing machine this is all middle class budget item\nThank you Flipkart 👍👍",
            "reviewer": "Harsh Srivastava",
            "reviewer_location": ", Fatehpur Fatehpur District",
            "indexed_at": "2024-11-11T19:23:09.322736",
            "updated_at": "2024-11-11T19:23:09.322736"
        },
        ]
    }
