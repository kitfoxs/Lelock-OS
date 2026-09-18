"""Small, dependency-free primitives. POSIX desktop reference implementation."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

class EntityError(RuntimeError):
    """An expected refusal or failure; callers must not claim an effect succeeded."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw: str | bytes, *, max_bytes: int = 2_000_000) -> Any:
    if len(raw.encode() if isinstance(raw, str) else raw) > max_bytes:
        raise EntityError("JSON exceeds the byte budget")
    def pairs(items):
        out = {}
        for key, val in items:
            if key in out:
                raise EntityError("Duplicate JSON key")
            out[key] = val
        return out
    def bad_constant(value):
        raise EntityError("Non-finite JSON number")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EntityError("Invalid JSON") from exc


def private_dir(path: Path) -> Path:
    path = Path(path).absolute()
    if path.is_symlink():
        raise EntityError("State directory cannot be a symlink")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise EntityError("Expected a directory")
    path.chmod(0o700)
    return path


def write_new_private(path: Path, data: bytes) -> None:
    """Never replace another file. Parent must be an operator-selected private directory."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)


def text(value: Any, maximum: int = 64_000, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value) or len(value.encode()) > maximum:
        raise EntityError("Expected bounded text")
    return value


def validate(schema: dict, value: Any, depth: int = 0) -> None:
    """The deliberate JSON Schema subset used by this package, NOT a full validator."""
    if depth > 20:
        raise EntityError("Input nesting exceeds the budget")
    typ = schema.get("type")
    checks = {"object": lambda: isinstance(value, dict),
              "array": lambda: isinstance(value, list),
              "string": lambda: isinstance(value, str),
              "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
              "number": lambda: isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value),
              "boolean": lambda: isinstance(value, bool), "null": lambda: value is None}
    if typ not in checks or not checks[typ]():
        raise EntityError(f"Expected {typ}")
    if "enum" in schema and value not in schema["enum"]:
        raise EntityError("Value outside enum")
    if typ == "object":
        props = schema.get("properties", {})
        if not set(schema.get("required", [])) <= value.keys():
            raise EntityError("Required field missing")
        if schema.get("additionalProperties", False) is False and not value.keys() <= props.keys():
            raise EntityError("Unknown field")
        for key, val in value.items():
            if key in props:
                validate(props[key], val, depth + 1)
    elif typ == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 1000):
            raise EntityError("Array size outside bounds")
        for val in value:
            validate(schema["items"], val, depth + 1)
    elif typ == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 100_000):
            raise EntityError("String length outside bounds")
    elif typ in {"integer", "number"}:
        if not schema.get("minimum", -math.inf) <= value <= schema.get("maximum", math.inf):
            raise EntityError("Number outside bounds")


def object_schema(properties: dict, required: tuple | list = ()) -> dict:
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}

STRING = {"type": "string", "maxLength": 64_000}
