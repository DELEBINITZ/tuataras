from fastapi import APIRouter
from core.worker.tasks import extract_review
reviews_router = APIRouter()

@reviews_router.get("/reviews")
def extract_reviews():
  print("here")
  extract_review.delay("first task from celert")
  pass
