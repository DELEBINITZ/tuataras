from pydantic import BaseModel, Field

class Health(BaseModel):
  version: str = Field(...)
  status: str = Field(...)