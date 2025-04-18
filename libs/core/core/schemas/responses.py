from typing import Generic

from fastapi import status as http_status
from pydantic import BaseModel, ConfigDict, Field

from core.annotations import ModelInstance, ResultObject, SchemaInstance, StrOrNone
from core.enums import JSENDStatus
from core.schemas.requests import BaseRequestSchema


class BaseResponseSchema(BaseRequestSchema):
    """Base schema for schemas that will be used in responses."""

    model_config = ConfigDict(
        validate_assignment=True,
        from_attributes=True,
        strict=False,
        defer_build=True,
        extra="ignore",
    )

    # TODO: Move to BaseService class.
    @classmethod
    def from_model(cls, obj: SchemaInstance) -> ModelInstance:
        return cls.model_validate(obj=obj, strict=False, from_attributes=True)


class JSENDResponseSchema(BaseModel, Generic[SchemaInstance]):
    """JSEND schema with 'success' status."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": JSENDStatus.SUCCESS, "data": {}, "code": 200},
            ],
        },
    )

    status: JSENDStatus = Field(default=JSENDStatus.SUCCESS)
    data: SchemaInstance | None = Field(default=None)
    message: str = Field(default=...)
    code: int = Field(default=http_status.HTTP_200_OK)


class JSENDFailResponseSchema(JSENDResponseSchema[SchemaInstance]):
    """JSEND schema with 'fail' status (validation errors, client errors)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": JSENDStatus.FAIL, "data": {}, "code": 422},
            ],
        },
    )

    status: JSENDStatus = Field(default=JSENDStatus.FAIL)
    data: SchemaInstance = Field(default=None)


class JSENDErrorResponseSchema(JSENDResponseSchema[SchemaInstance]):
    """JSEND schema with 'error' status (server errors)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": JSENDStatus.ERROR, "data": None, "message": "Internal server error.", "code": 500},
            ],
        },
    )

    status: JSENDStatus = Field(default=JSENDStatus.ERROR)
    data: SchemaInstance = Field(default=None)


class UnprocessableEntityResponseSchema(BaseResponseSchema):
    """Schema that uses in pydantic validation errors."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": JSENDStatus.FAIL,
                    "data": {
                        "location": ["body", "fieldOne"],
                        "message": "Field required.",
                        "type": "missing",
                        "context": None,
                    },
                    "message": "Validation error.",
                    "code": 422,
                },
            ],
        },
    )

    location: list[str] = Field(description="Depth list of field that caused the error.")
    message: str = Field(description="Message that describes the error.")
    type: str = Field(description="Type of the error.")
    context: StrOrNone = Field(default=None, description="Additional context for the error.")


class PaginationResponseSchema(BaseModel, Generic[ResultObject]):
    """Generic ResponseSchema that uses for pagination."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    objects: list[ResultObject]
    offset: int | None = Field(default=None, description="Number of objects to skip.")
    limit: int = Field(default=100, description="Number of objects returned per one page.")
    total_count: int = Field(
        default=...,
        alias="totalCount",
        description="Numbed of objects counted inside db for this query.",
    )
    next_token: StrOrNone = Field(
        default=None,
        alias="nextToken",
        title="Next Token",
        description="This is the latest `id` of previous result.",
    )
    page: int | None = Field(default=None, title="Page", description="Current page (depends on offset, limit).")
    pages: int | None = Field(
        default=None,
        title="Pages",
        description="Total number of pages (depends on limit and total number of records).",
    )


class JSENDPaginationResponseSchema(JSENDResponseSchema[SchemaInstance]):
    """Cover PaginationOutSchema with JSEND structure."""

    data: PaginationResponseSchema[SchemaInstance] = Field(default=...)
