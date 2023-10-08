from pydantic import BaseModel, Field

class SqlParser(BaseModel):
    input_query: str = Field(min_length=1)