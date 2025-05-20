from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    id: int = Field()
    username: str = Field(min_length=3, max_length=16)
