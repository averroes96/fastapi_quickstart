import datetime
import functools
import json
import typing
import uuid

import orjson
import uuid_extensions
import zoneinfo
from fastapi.encoders import jsonable_encoder


@functools.lru_cache
def get_utc_timezone() -> zoneinfo.ZoneInfo:
    """Return UTC zone info."""
    return zoneinfo.ZoneInfo(key="UTC")


def utc_now() -> datetime.datetime:
    """Return current datetime with UTC zone info."""
    return datetime.datetime.now(tz=get_utc_timezone())


def as_utc(date_time: datetime.datetime) -> datetime.datetime:
    """Get datetime object and convert it to datetime with UTC zone info."""
    return date_time.astimezone(tz=get_utc_timezone())


def id_v1() -> str:
    """Generate UUID with version 1 (can extract created_at datetime)."""
    return str(uuid.uuid1())


def id_v4() -> str:
    """Generate UUID with version 4."""
    return str(uuid.uuid4())


def id_v7() -> str:
    """Generate UUID with version 7."""
    return uuid_extensions.uuid7str()


def orjson_dumps(v: typing.Any, *, default: json.JSONEncoder) -> str:
    """Transforms python-data to JSON-like string.

    Args:
        v (Any): Value that should be dumped into the JSON.
        default (json.JSONEncoder): JSON encoder instance to customize transformation behavior.

    Returns:
        (str): JSON-like string.
    """
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode(encoding="utf-8")


def get_timestamp(v: datetime.datetime) -> float:
    """Extract timestamp from datetime object and round for 3 decimal digits."""
    return round(v.timestamp(), 3)


def proxy_func(x: typing.Any) -> typing.Any:
    """Function that proxies value back (doing nothing)."""
    return x


encodings_dict: dict[typing.Any, typing.Callable[[typing.Any], typing.Any]] = {
    datetime.datetime: proxy_func,  # don't transform datetime object.
    datetime.date: proxy_func,  # don't transform date objects.
}
to_db_encoder = functools.partial(
    jsonable_encoder,
    exclude_unset=True,
    by_alias=False,
    custom_encoder=encodings_dict,  # override `jsonable_encoder` default behaviour.
)


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj: typing.Any) -> str:
        if isinstance(obj, uuid.UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        elif isinstance(obj, datetime.datetime):  # noqa: RET505
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class ExtendedJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(object_hook=self._iso_datetime_decoder, *args, **kwargs)

    def _iso_datetime_decoder(self, dct: dict[str, str]) -> dict[str, str | datetime.datetime]:
        for key, value in dct.items():
            if isinstance(value, str):
                try:
                    iso_datetime = datetime.datetime.fromisoformat(value)
                    dct[key] = iso_datetime
                except ValueError:
                    ...
        return dct
