from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractReviewRequest(BaseModel):
    url: str = Field(...)

class ReviewerDetails(BaseModel):
    location: Optional[str] = None

class ReviewDTO(BaseModel):
    review_id: str
    product_name: str
    site_name: str
    rating: float
    title: str
    description: str
    reviewer: str
    reviewer_location: Optional[str] = None
    indexed_at: str
    updated_at: str

class PaginatedResponse(BaseModel):
    status: str
    page: int
    page_size: int
    total_results: int
    total_pages: int
    reviews: List[ReviewDTO]
