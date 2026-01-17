from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from scraparse.core.util import snake_case
from scraparse.core.limits import Limits

FieldType = Literal["string", "number", "money", "date", "url", "boolean"]
ALLOWED_FIELD_TYPES: set[str] = {"string", "number", "money", "date", "url", "boolean"}


@dataclass
class FieldSpec:
    name: str
    type: FieldType
    required: bool
    description: str = ""
    example: str = ""

    def normalized(self) -> "FieldSpec":
        return FieldSpec(
            name=snake_case(self.name),
            type=self.type,
            required=self.required,
            description=self.description,
            example=self.example,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "example": self.example,
        }


@dataclass
class FieldSchema:
    fields: list[FieldSpec] = field(default_factory=list)

    def normalized(self) -> "FieldSchema":
        return FieldSchema(fields=[field.normalized() for field in self.fields])

    def to_dict(self) -> dict[str, object]:
        return {"fields": [field.to_dict() for field in self.fields]}

    @staticmethod
    def from_dict(data: dict[str, object]) -> "FieldSchema":
        raw_fields = data.get("fields")
        if not isinstance(raw_fields, list):
            raise ValueError("Schema JSON must include a 'fields' list")
        fields: list[FieldSpec] = []
        for raw in raw_fields:
            if not isinstance(raw, dict):
                raise ValueError("Each field must be an object")
            name = str(raw.get("name", "")).strip()
            field_type = str(raw.get("type", "")).strip()
            required = bool(raw.get("required", False))
            description = str(raw.get("description", ""))
            example = str(raw.get("example", ""))
            if field_type not in ALLOWED_FIELD_TYPES:
                raise ValueError(f"Invalid field type: {field_type}")
            fields.append(
                FieldSpec(
                    name=name,
                    type=field_type,  # type: ignore[arg-type]
                    required=required,
                    description=description,
                    example=example,
                )
            )
        return FieldSchema(fields=fields).normalized()


@dataclass
class RunSpec:
    url: str
    discover: bool
    discover_strategy: str
    prompt: str
    context: str
    promptpack: str
    save_artifacts: bool
    mode: str
    limits: Limits
    next_selector: Optional[str] = None
    detail_selector: Optional[str] = None


@dataclass
class FetchResult:
    url: str
    content_bytes: bytes
    content_text: str
    status_code: int
    content_type: str


@dataclass
class RunOutcome:
    run_id: str
    parser_path: str
    report_path: str
    fetched_urls: list[str]
    errors: list[str]
