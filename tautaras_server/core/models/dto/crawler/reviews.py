from pydantic import BaseModel, Field


class ExtractReviewRequest(BaseModel):
    url: str = Field(...)
