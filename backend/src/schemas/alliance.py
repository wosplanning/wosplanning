from pydantic import BaseModel, Field
from typing import Optional


class AllianceSchema(BaseModel):
    id: int = Field()
    tag: Optional[str] = Field(None, min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
