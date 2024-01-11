from typing import Optional
from pydantic import BaseModel, Field

"""
class MyPydanticModel(BaseModel):
    title: Optional[str] = Field(None, max_length=10)

class MyPydanticModel(BaseModel):
    title: str = Field(..., max_length=10)

"""


class UserRegisterRequestBodyModel(BaseModel):
    username: str = Field(..., max_length=256)
    password: str = Field(..., max_length=512)
    email: str = Field(None, max_length=128)
    first_name: Optional[str] = Field(None, max_length=128)
    last_name: Optional[str] = Field(None, max_length=128)
    phone_number: Optional[str] = Field(None, max_length=128)


class UserLoginBodyModel(BaseModel):
    email: str = Field(..., max_length=256)
    code: Optional[str] = Field(None, max_length=6)
