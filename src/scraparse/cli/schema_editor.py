from __future__ import annotations

from scraparse.core.errors import ConfigError
from scraparse.core.models import ALLOWED_FIELD_TYPES, FieldSchema, FieldSpec
from scraparse.core.util import snake_case


class SchemaEditor:
    def confirm(self, schema: FieldSchema) -> FieldSchema:
        current = schema
        while True:
            self._print_schema(current)
            print("\nOptions: [a]dd  [e]dit  [r]emove  [t]oggle required  [c]hange type  [y]confirm  [q]quit")
            choice = input("Select: ").strip().lower()
            try:
                if choice == "a":
                    current = self._add_field(current)
                elif choice == "e":
                    current = self._edit_field(current)
                elif choice == "r":
                    current = self._remove_field(current)
                elif choice == "t":
                    current = self._toggle_required(current)
                elif choice == "c":
                    current = self._change_type(current)
                elif choice == "y":
                    return current
                elif choice == "q":
                    raise ConfigError("Schema confirmation aborted by user")
                else:
                    print("Invalid choice")
            except ValueError as exc:
                print(f"Invalid input: {exc}")

    def _print_schema(self, schema: FieldSchema) -> None:
        print("\nCurrent schema:")
        for idx, field in enumerate(schema.fields, start=1):
            required = "required" if field.required else "optional"
            print(
                f"{idx}. {field.name} ({field.type}, {required}) - {field.description} "
                f"example: {field.example}"
            )

    def _select_index(self, schema: FieldSchema) -> int:
        value = input("Field number: ").strip()
        index = int(value) - 1
        if index < 0 or index >= len(schema.fields):
            raise ValueError("Invalid field number")
        return index

    def _add_field(self, schema: FieldSchema) -> FieldSchema:
        name = snake_case(input("Name: ").strip())
        field_type = input(f"Type {sorted(ALLOWED_FIELD_TYPES)}: ").strip()
        if field_type not in ALLOWED_FIELD_TYPES:
            raise ValueError("Invalid field type")
        required = input("Required? [y/n]: ").strip().lower() in {"y", "yes"}
        description = input("Description: ").strip()
        example = input("Example: ").strip()
        new_field = FieldSpec(
            name=name,
            type=field_type,  # type: ignore[arg-type]
            required=required,
            description=description,
            example=example,
        )
        return FieldSchema(fields=[*schema.fields, new_field])

    def _edit_field(self, schema: FieldSchema) -> FieldSchema:
        index = self._select_index(schema)
        field = schema.fields[index]
        name = input(f"Name [{field.name}]: ").strip() or field.name
        description = input(f"Description [{field.description}]: ").strip() or field.description
        example = input(f"Example [{field.example}]: ").strip() or field.example
        updated = FieldSpec(
            name=snake_case(name),
            type=field.type,
            required=field.required,
            description=description,
            example=example,
        )
        new_fields = list(schema.fields)
        new_fields[index] = updated
        return FieldSchema(fields=new_fields)

    def _remove_field(self, schema: FieldSchema) -> FieldSchema:
        index = self._select_index(schema)
        new_fields = [field for idx, field in enumerate(schema.fields) if idx != index]
        return FieldSchema(fields=new_fields)

    def _toggle_required(self, schema: FieldSchema) -> FieldSchema:
        index = self._select_index(schema)
        field = schema.fields[index]
        updated = FieldSpec(
            name=field.name,
            type=field.type,
            required=not field.required,
            description=field.description,
            example=field.example,
        )
        new_fields = list(schema.fields)
        new_fields[index] = updated
        return FieldSchema(fields=new_fields)

    def _change_type(self, schema: FieldSchema) -> FieldSchema:
        index = self._select_index(schema)
        field = schema.fields[index]
        field_type = input(f"Type {sorted(ALLOWED_FIELD_TYPES)}: ").strip()
        if field_type not in ALLOWED_FIELD_TYPES:
            raise ValueError("Invalid field type")
        updated = FieldSpec(
            name=field.name,
            type=field_type,  # type: ignore[arg-type]
            required=field.required,
            description=field.description,
            example=field.example,
        )
        new_fields = list(schema.fields)
        new_fields[index] = updated
        return FieldSchema(fields=new_fields)
