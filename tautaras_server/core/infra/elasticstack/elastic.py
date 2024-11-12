from elasticsearch import Elasticsearch, NotFoundError
from typing import Optional
import logging

from core.config.env_config import sttgs

client = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_client() -> Elasticsearch:
    global client
    if not client:
        logger.info("Attempting to connect to Elasticsearch...")
        try:
            client = Elasticsearch(
                hosts=sttgs.get("ES_HOST"),
                basic_auth=(sttgs.get("ES_USER"), sttgs.get("ES_PASS")),
                ca_certs=False,
                verify_certs=False,
                ssl_show_warn=False,
            )

            if not client.ping():
                raise ConnectionError("Failed to connect to Elasticsearch.")

            logger.info("Successfully connected to Elasticsearch.")

        except Exception as e:
            logger.error(f"Elasticsearch connection error: {e}")
            client = None
            return None

    return client


async def create_document(index_name: str, doc_id: str, document: dict):
    try:
        es_client = get_client()
        response = es_client.index(index=index_name, id=doc_id, body=document)
        logger.info(f"Document created in index '{index_name}' with ID '{doc_id}'.")
        return response, None
    except Exception as e:
        logger.error(
            f"Error creating document in index '{index_name}' with ID '{doc_id}': {e}"
        )
        return None, e


async def read_document(index_name: str, doc_id: str):
    try:
        es_client = get_client()
        response = es_client.get(index=index_name, id=doc_id)
        logger.info(f"Document read from index '{index_name}' with ID '{doc_id}'.")
        return response["_source"]
    except Exception as e:
        logger.error(
            f"Error reading document from index '{index_name}' with ID '{doc_id}': {e}"
        )
        return None


def update_document(index_name: str, doc_id: str, new_data: dict):
    try:
        es_client = get_client()
        response = es_client.update(index=index_name, id=doc_id, body={"doc": new_data})
        logger.info(f"Document updated in index '{index_name}' with ID '{doc_id}'.")
        return response
    except Exception as e:
        logger.error(
            f"Error updating document in index '{index_name}' with ID '{doc_id}': {e}"
        )
        return None


def delete_document(index_name: str, doc_id: str):
    try:
        es_client = get_client()
        response = es_client.delete(index=index_name, id=doc_id)
        logger.info(f"Document deleted from index '{index_name}' with ID '{doc_id}'.")
        return response
    except Exception as e:
        logger.error(
            f"Error deleting document from index '{index_name}' with ID '{doc_id}': {e}"
        )
        return None


async def document_exists(index_name: str, doc_id: str):
    es_client = get_client()
    try:
        es_client.get(index=index_name, id=doc_id)
        return True
    except NotFoundError:
        return False
    except Exception as e:
        logger.error(f"Error checking existence of document with ID '{doc_id}': {e}")
        return False  


def search_documents(index_name: str, query: dict, size: int = 10):
    try:
        es_client = get_client()
        response = es_client.search(index=index_name, body=query, size=size)
        logger.info(f"Search executed on index '{index_name}' with query '{query}'.")
        return response["hits"]["hits"]
    except Exception as e:
        logger.error(f"Error searching documents in index '{index_name}': {e}")
        return None
