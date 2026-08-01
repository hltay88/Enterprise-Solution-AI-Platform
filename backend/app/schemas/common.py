"""Shared API schema types."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    error: ErrorBody | None = None


class HealthData(BaseModel):
    status: str = Field(examples=["ok"])
    database: str = Field(examples=["not_configured"])
