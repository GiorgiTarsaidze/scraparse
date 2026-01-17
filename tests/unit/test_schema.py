import pytest

from scraparse.core.models import FieldSchema


def test_schema_normalizes_names() -> None:
    data = {
        "fields": [
            {
                "name": "Product Name",
                "type": "string",
                "required": True,
                "description": "Name",
                "example": "Widget",
            }
        ]
    }
    schema = FieldSchema.from_dict(data)
    assert schema.fields[0].name == "product_name"


def test_schema_rejects_invalid_type() -> None:
    data = {
        "fields": [
            {
                "name": "price",
                "type": "invalid",
                "required": True,
                "description": "Price",
                "example": "9.99",
            }
        ]
    }
    with pytest.raises(ValueError):
        FieldSchema.from_dict(data)
