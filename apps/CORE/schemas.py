import datetime
import uuid
from typing import Generic

import orjson
import pydantic.json
from fastapi import status as http_status
from pydantic import AnyHttpUrl, BaseModel, Field, validate_model
from pydantic.generics import GenericModel
from pydantic.main import object_setattr

from apps.CORE.enums import JSENDStatus
from apps.CORE.types import ModelType, ObjectsVar, SchemaType, StrOrNone, StrUUID, Timestamp
from apps.CORE.utils import get_timestamp, orjson_dumps


class BaseInSchema(BaseModel):
    """Base schema for schemas that will be used in request validations."""

    class Config:
        """Schema configuration."""

        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True
        allow_population_by_field_name = True
        use_enum_values = True


class BaseOutSchema(BaseInSchema):
    """Base schema for schemas that will be used in responses."""

    class Config(BaseInSchema.Config):
        """Schema configuration."""

        json_encoders = {
            # field type: encoder function
            datetime.datetime: get_timestamp,
            datetime.timedelta: lambda time_delta: pydantic.json.timedelta_isoformat(time_delta),
            uuid.UUID: str,
        }
        json_dumps = orjson_dumps
        json_loads = orjson.loads

    @classmethod
    def from_orm(cls, obj: SchemaType) -> ModelType:
        # TableNameMixin.to_dict() logic.
        obj = obj.to_dict()
        # Pydantic from_orm logic.
        model = cls.__new__(cls)
        values, fields_set, validation_error = validate_model(cls, obj)
        if validation_error:
            raise validation_error
        object_setattr(model, "__dict__", values)
        object_setattr(model, "__fields_set__", fields_set)
        model._init_private_attributes()
        return model


class JSENDOutSchema(GenericModel, Generic[SchemaType]):
    """JSEND schema with 'success' status."""

    status: JSENDStatus = Field(default=JSENDStatus.SUCCESS)
    data: SchemaType | None = Field(default=None)
    message: str = Field(default=...)
    code: int = Field(default=http_status.HTTP_200_OK)


class JSENDFailOutSchema(JSENDOutSchema):
    """JSEND schema with 'fail' status (validation errors, client errors)."""

    status: JSENDStatus = Field(default=JSENDStatus.FAIL)
    data: StrOrNone = Field(default=None)


class JSENDErrorOutSchema(JSENDOutSchema):
    """JSEND schema with 'error' status (server errors)."""

    status: JSENDStatus = Field(default=JSENDStatus.ERROR)
    data: StrOrNone = Field(default=None)


class UnprocessableEntityOutSchema(BaseOutSchema):
    """Schema that uses in pydantic validation errors."""

    location: list[str] = Field(example=["body", "field_1"])
    message: str = Field(example="Field required.")
    type: str = Field(example="value_error.missing")
    context: StrOrNone = Field(default=None)


class CreatedAtOutSchema(BaseModel):
    """Schema with `createdAt` Timestamp field."""

    created_at: Timestamp = Field(title="Created at", alias="createdAt")


class UpdatedAtOutSchema(BaseModel):
    """Schema with `updatedAt` Timestamp field."""

    updated_at: Timestamp = Field(title="Updated at", alias="updatedAt")


class CreatedUpdatedOutSchema(CreatedAtOutSchema, UpdatedAtOutSchema):
    """Schema with `createdAt` and `updatedAt` Timestamp fields."""

    ...


class PaginationOutSchema(GenericModel, Generic[ObjectsVar]):
    """Generic OurSchema that uses for pagination."""

    objects: list[ObjectsVar]
    offset: int | None = Field(default=None, description="Number of objects to skip.")
    limit: int = Field(default=100, description="Number of objects returned per one page.")
    count: int = Field(default=0, alias="objectsCount", description="Number of objects returned in this response.")
    total_count: int = Field(
        default=..., alias="totalCount", description="Numbed of objects counted inside db for this query."
    )
    next_token: StrUUID | None = Field(
        default=None,
        alias="nextToken",
        title="Next Token",
        description="This is the latest `id` of previous result.",
    )
    next_url: AnyHttpUrl | None = Field(default=None, alias="nextURL", title="Next URL")
    previous_url: AnyHttpUrl | None = Field(default=None, alias="previousURL", title="Previous URL")
    page: int | None = Field(default=None, title="Page", description="Current page (depends on offset, limit).")
    pages: int = Field(
        default=..., title="Pages", description="Total number of pages (depends on limit and total number of records)."
    )

    class Config(BaseOutSchema.Config):
        """
        `allow_population_by_field_name` used only for remove lint error from PyCharm
        (by default it applies from BaseOutSchema.Config inheritance).

        It also can be defined as:
        ```python
        class Config(BaseOutSchema.Config):
            ...
        ```
        """

        allow_population_by_field_name = True


class JSENDPaginationOutSchema(JSENDOutSchema):
    """Cover PaginationOutSchema with JSEND structure."""

    data: PaginationOutSchema = Field(default=...)


class TokenPayloadSchema(BaseOutSchema):
    """Base JWT token payloads."""

    iat: Timestamp
    aud: str
    exp: Timestamp
    nbf: Timestamp
    iss: str


class TokenOptionsSchema(BaseOutSchema):
    """Schema options for PyJWT parsing & validation.

    Attributes:
        verify_signature (bool): Toggle validation for PyJWT library. Defaults: `True`

            `True` --> Enabled,

            `False` --> Disabled.

        require (list[str]): Force check these keys inside JWT's payload.

            Defaults: `["aud", "exp", "iat", "iss", "nbf"]`
        verify_aud (bool): Enable validation for `aud` field. Defaults: `True`
        verify_exp (bool): Enable validation for `exp` field. Defaults: `True`
        verify_iat (bool): Enable validation for `iat` field. Defaults: `True`
        verify_iss (bool): Enable validation for `iss` field. Defaults: `True`
        verify_nbf (bool): Enable validation for `nbf` field. Defaults: `True`
    Examples:
        Initialize schema (default attributes).
        >>> schema_1 = TokenOptionsSchema()

        Initialize schema (disable validation).
        >>> schema_2 = TokenOptionsSchema(verify_signature=False)

        Initialize schema (force require only `aud` as a required key and disable validation for `exp` key).
        >>> schema_2 = TokenOptionsSchema(requre=["aud"], verify_exp=False)
    """

    verify_signature: bool = Field(default=True)
    requre: list[str] = Field(default=["aud", "exp", "iat", "iss", "nbf"])  # pyJWT default is: []
    verify_aud: bool = Field(default=True)
    verify_exp: bool = Field(default=True)
    verify_iat: bool = Field(default=True)
    verify_iss: bool = Field(default=True)
    verify_nbf: bool = Field(default=True)
