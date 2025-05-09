import pytest
from core.enums import JSENDStatus
from core.exceptions import BackendError
from faker import Faker
from fastapi import status


class TestBackendException:
    def test__repr___defaults(self, faker: Faker) -> None:
        message = faker.pystr()
        exception = BackendError(message=message)

        assert (
            repr(exception) == f'{BackendError.__name__}(status={exception.status}, data={exception.data}, message="'
            f'{exception.message}", code={exception.code})'
        )

    @pytest.mark.parametrize(
        argnames=("jsend_status", "faker_func", "code"),
        argvalues=(
            (JSENDStatus.SUCCESS, "pydict", status.HTTP_200_OK),
            (JSENDStatus.SUCCESS, "pylist", status.HTTP_201_CREATED),
            (JSENDStatus.FAIL, "pydecimal", status.HTTP_400_BAD_REQUEST),
            (JSENDStatus.FAIL, "pystr", status.HTTP_404_NOT_FOUND),
            (JSENDStatus.ERROR, "pybool", status.HTTP_500_INTERNAL_SERVER_ERROR),
            (JSENDStatus.ERROR, "pyfloat", status.HTTP_501_NOT_IMPLEMENTED),
        ),
    )
    def test__repr__custom(self, jsend_status: JSENDStatus, faker_func: str, code: int, faker: Faker) -> None:
        fake_data = getattr(faker, faker_func)()
        fake_message = faker.pystr()

        exception = BackendError(status=jsend_status, data=fake_data, message=fake_message, code=code)

        assert exception.status == jsend_status
        assert exception.data == fake_data
        assert exception.message == fake_message
        assert exception.code == code
        assert (
            repr(exception) == f'{BackendError.__name__}(status={exception.status}, data={exception.data}, message="'
            f'{exception.message}", code={exception.code})'
        )

    def test__str___defaults(self, faker: Faker) -> None:
        message = faker.pystr()
        exception = BackendError(message=message)

        assert (
            str(exception) == f'{BackendError.__name__}(status={exception.status}, data={exception.data}, message="'
            f'{exception.message}", code={exception.code})'
        )

    def test_dict_default(self, faker: Faker) -> None:
        message = faker.pystr()
        exception = BackendError(message=message)

        result = exception.dict()

        assert result == {
            "status": JSENDStatus.FAIL,
            "data": exception.data,
            "message": exception.message,
            "code": exception.code,
        }

    @pytest.mark.parametrize(
        argnames=("jsend_status", "faker_func", "code"),
        argvalues=(
            (JSENDStatus.SUCCESS, "pydict", status.HTTP_200_OK),
            (JSENDStatus.SUCCESS, "pylist", status.HTTP_201_CREATED),
            (JSENDStatus.FAIL, "pydecimal", status.HTTP_400_BAD_REQUEST),
            (JSENDStatus.FAIL, "pystr", status.HTTP_404_NOT_FOUND),
            (JSENDStatus.ERROR, "pybool", status.HTTP_500_INTERNAL_SERVER_ERROR),
            (JSENDStatus.ERROR, "pyfloat", status.HTTP_501_NOT_IMPLEMENTED),
        ),
    )
    def test_dict_custom(self, jsend_status: JSENDStatus, faker_func: str, code: int, faker: Faker) -> None:
        fake_data = getattr(faker, faker_func)()
        fake_message = faker.pystr()

        exception = BackendError(status=jsend_status, data=fake_data, message=fake_message, code=code)

        assert exception.status == jsend_status
        assert exception.data == fake_data
        assert exception.message == fake_message
        assert exception.code == code
        assert exception.dict() == {"status": jsend_status, "data": fake_data, "message": fake_message, "code": code}
