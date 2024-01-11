from typing import Optional
from pydantic import BaseModel, Field

"""
class MyPydanticModel(BaseModel):
    title: Optional[str] = Field(None, max_length=10)

class MyPydanticModel(BaseModel):
    title: str = Field(..., max_length=10)

"""


class PaginatorModel(BaseModel):
    page: Optional[int] = 0
    per_page: Optional[int] = 10
    search: Optional[str] = ""
