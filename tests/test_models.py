from io import BytesIO

import pytest

from fires3.models import Object


@pytest.fixture
def object_data():
    def fake_loader():
        return BytesIO(b"test content")

    object = Object("key", fake_loader)

    return object, b"test content"


def test_object(object_data):
    object, content = object_data

    assert object.key
    assert object.content
    assert object.content.getvalue() == content
