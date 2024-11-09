from .celery_app import celery_app

@celery_app.task
def extract_review(message):
  print("thos os running from celery", message)
