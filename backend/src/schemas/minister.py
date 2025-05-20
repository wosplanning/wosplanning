from pydantic import BaseModel, Field
from typing import Optional


class MinisterSchema(BaseModel):
    id: int = Field()
    type: int = Field()
    name: Optional[str] = Field(None, min_length=3, max_length=32)
