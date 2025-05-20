from pydantic import BaseModel, Field


class StateSchema(BaseModel):
    id: int = Field()
