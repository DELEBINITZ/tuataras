from elasticsearch import Elasticsearch
from typing import Optional

from core.config import sttgs

client = None

def get_client() -> Elasticsearch:
    global client
    if not client:
        client = Elasticsearch(
            hosts=sttgs.get("ES_HOSTS"),
            basic_auth=(sttgs.get("ES_USER"), sttgs.get("ES_PASS")),
            ca_certs=False,
            verify_certs=False,
        )
    return client


async def create_document(index_name: str, doc_id: str, document: dict):
    try:
        es_client = get_client()
        response = es_client.index(index=index_name, id=doc_id, body=document)
        return response, None
    except Exception as e:
        print(f"Error creating document: {e}")
        return None, e


async def read_document(index_name: str, doc_id: str):
    try:
        es_client = get_client()
        response = await es_client.get(index=index_name, id=doc_id)
        return response["_source"]
    except Exception as e:
        print(f"Error reading document: {e}")
        return None


def update_document(index_name: str, doc_id: str, new_data: dict):
    try:
        es_client = get_client()
        response = es_client.update(index=index_name, id=doc_id, body={"doc": new_data})
        return response
    except Exception as e:
        print(f"Error updating document: {e}")
        return None


def delete_document(index_name: str, doc_id: str):
    try:
        es_client = get_client()
        response = es_client.delete(index=index_name, id=doc_id)
        return response
    except Exception as e:
        print(f"Error deleting document: {e}")
        return None


def search_documents(index_name: str, query: dict, size: Optional[int] = 10):
    try:
        es_client = get_client()
        response = es_client.search(index=index_name, body=query, size=size)
        return response["hits"]["hits"]
    except Exception as e:
        print(f"Error searching documents: {e}")
        return None
