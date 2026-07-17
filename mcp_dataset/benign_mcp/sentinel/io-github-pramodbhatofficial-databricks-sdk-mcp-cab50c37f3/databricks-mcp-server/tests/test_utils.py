"""Tests for databricks_mcp.utils — serialize, paginate, truncate_results, format_error, to_json."""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pytest

from databricks_mcp.utils import (
    format_error,
    paginate,
    serialize,
    to_json,
    truncate_results,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class Color(Enum):
    RED = "red"
    GREEN = "green"


@dataclass
class Address:
    city: str
    zip_code: str


@dataclass
class Person:
    name: str
    age: int
    address: Address | None = None


class PlainObject:
    """A non-dataclass object with __dict__."""

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self._internal = "hidden"


# ---------------------------------------------------------------------------
# serialize()
# ---------------------------------------------------------------------------

class TestSerialize:
    """Verify serialize() handles the full spectrum of types."""

    def test_none(self) -> None:
        assert serialize(None) is None

    def test_primitives(self) -> None:
        assert serialize("hello") == "hello"
        assert serialize(42) == 42
        assert serialize(3.14) == 3.14
        assert serialize(True) is True
        assert serialize(False) is False

    def test_dict(self) -> None:
        result = serialize({"a": 1, "b": "two"})
        assert result == {"a": 1, "b": "two"}

    def test_nested_dict(self) -> None:
        result = serialize({"outer": {"inner": 99}})
        assert result == {"outer": {"inner": 99}}

    def test_list(self) -> None:
        result = serialize([1, "two", 3.0])
        assert result == [1, "two", 3.0]

    def test_tuple(self) -> None:
        # Tuples are serialized as lists
        result = serialize((1, 2, 3))
        assert result == [1, 2, 3]

    def test_dataclass_simple(self) -> None:
        person = Person(name="Alice", age=30)
        result = serialize(person)
        assert result == {"name": "Alice", "age": 30}
        # address is None and should be excluded
        assert "address" not in result

    def test_dataclass_nested(self) -> None:
        person = Person(name="Bob", age=25, address=Address(city="NYC", zip_code="10001"))
        result = serialize(person)
        assert result == {
            "name": "Bob",
            "age": 25,
            "address": {"city": "NYC", "zip_code": "10001"},
        }

    def test_enum(self) -> None:
        assert serialize(Color.RED) == "red"
        assert serialize(Color.GREEN) == "green"

    def test_object_with_dict(self) -> None:
        obj = PlainObject(x=10, y=20)
        result = serialize(obj)
        assert result == {"x": 10, "y": 20}
        # Attributes starting with _ should be excluded
        assert "_internal" not in result

    def test_object_with_dict_none_values_excluded(self) -> None:
        """None values in __dict__ objects are excluded."""
        obj = PlainObject(x=1, y=2)
        obj.z = None  # type: ignore[attr-defined]
        result = serialize(obj)
        assert "z" not in result

    def test_list_of_dataclasses(self) -> None:
        people = [Person(name="A", age=1), Person(name="B", age=2)]
        result = serialize(people)
        assert len(result) == 2
        assert result[0] == {"name": "A", "age": 1}
        assert result[1] == {"name": "B", "age": 2}

    def test_fallback_to_str(self) -> None:
        """Types without __dict__ or special handling fall through to str()."""
        # bytes has no .value and no __dict__ (in the sense that serialize checks),
        # but it does have __dict__ in CPython.  Use a custom object that lacks
        # .value and __dict__.
        result = serialize(42 + 3j)  # complex number
        assert result == str(42 + 3j)

    def test_dict_with_none_values_kept(self) -> None:
        """None values inside dicts are serialized (only dataclass/object filtering removes them)."""
        result = serialize({"key": None})
        assert result == {"key": None}


# ---------------------------------------------------------------------------
# paginate()
# ---------------------------------------------------------------------------

class TestPaginate:
    """Verify paginate() collects items and respects max_items."""

    def test_basic(self) -> None:
        items = iter(["a", "b", "c"])
        result = paginate(items)
        assert result == ["a", "b", "c"]

    def test_max_items_limit(self) -> None:
        items = iter(range(200))
        result = paginate(items, max_items=5)
        assert len(result) == 5
        assert result == [0, 1, 2, 3, 4]

    def test_default_max_items_is_100(self) -> None:
        items = iter(range(150))
        result = paginate(items)
        assert len(result) == 100

    def test_empty_iterator(self) -> None:
        result = paginate(iter([]))
        assert result == []

    def test_serializes_items(self) -> None:
        """paginate() runs each item through serialize()."""
        people = [Person(name="X", age=10)]
        result = paginate(iter(people))
        assert result == [{"name": "X", "age": 10}]

    def test_max_items_zero(self) -> None:
        """max_items=0 should collect nothing."""
        result = paginate(iter([1, 2, 3]), max_items=0)
        assert result == []


# ---------------------------------------------------------------------------
# truncate_results()
# ---------------------------------------------------------------------------

class TestTruncateResults:
    """Verify truncate_results() wraps items with metadata."""

    def test_under_limit(self) -> None:
        items = [1, 2, 3]
        result = truncate_results(items, max_items=50)
        assert result == {"items": [1, 2, 3], "count": 3, "truncated": False}

    def test_at_limit(self) -> None:
        items = list(range(50))
        result = truncate_results(items, max_items=50)
        assert result["truncated"] is False
        assert result["count"] == 50
        assert len(result["items"]) == 50

    def test_over_limit(self) -> None:
        items = list(range(100))
        result = truncate_results(items, max_items=10)
        assert result["truncated"] is True
        assert result["count"] == 100
        assert len(result["items"]) == 10
        assert result["items"] == list(range(10))

    def test_default_max_items_is_50(self) -> None:
        items = list(range(60))
        result = truncate_results(items)
        assert result["truncated"] is True
        assert len(result["items"]) == 50
        assert result["count"] == 60

    def test_empty_list(self) -> None:
        result = truncate_results([])
        assert result == {"items": [], "count": 0, "truncated": False}


# ---------------------------------------------------------------------------
# format_error()
# ---------------------------------------------------------------------------

class TestFormatError:
    """Verify format_error() produces consistent error strings."""

    def test_standard_exception(self) -> None:
        err = ValueError("something went wrong")
        result = format_error(err)
        assert result == "ValueError: something went wrong"

    def test_exception_with_error_code(self) -> None:
        """Simulate Databricks API error with error_code attribute."""
        err = RuntimeError("resource not found")
        err.error_code = "RESOURCE_DOES_NOT_EXIST"  # type: ignore[attr-defined]
        result = format_error(err)
        assert result == "RuntimeError: [RESOURCE_DOES_NOT_EXIST] resource not found"

    def test_empty_message(self) -> None:
        err = Exception()
        result = format_error(err)
        assert result == "Exception: "

    def test_custom_exception_type(self) -> None:

        class MyCustomError(Exception):
            pass

        err = MyCustomError("oops")
        result = format_error(err)
        assert result == "MyCustomError: oops"


# ---------------------------------------------------------------------------
# to_json()
# ---------------------------------------------------------------------------

class TestToJson:
    """Verify to_json() returns well-formed JSON."""

    def test_dict(self) -> None:
        result = to_json({"key": "value"})
        parsed = json.loads(result)
        assert parsed == {"key": "value"}

    def test_indentation(self) -> None:
        result = to_json({"a": 1})
        # json.dumps with indent=2 should produce multi-line output
        assert "\n" in result

    def test_dataclass(self) -> None:
        person = Person(name="Alice", age=30)
        result = to_json(person)
        parsed = json.loads(result)
        assert parsed == {"name": "Alice", "age": 30}

    def test_list(self) -> None:
        result = to_json([1, 2, 3])
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_none(self) -> None:
        result = to_json(None)
        assert json.loads(result) is None

    def test_non_serializable_fallback(self) -> None:
        """Objects that json.dumps can't handle get str() via default=str."""
        result = to_json({"date": object()})
        parsed = json.loads(result)
        # The object should have been stringified
        assert isinstance(parsed["date"], str)
