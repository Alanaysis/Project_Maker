"""Metadata filtering for vector database queries."""

from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum


class FilterOperator(Enum):
    """Filter operators for metadata queries."""
    EQ = "eq"           # Equal
    NEQ = "neq"         # Not equal
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    IN = "in"           # Value in list
    NIN = "nin"         # Value not in list
    CONTAINS = "contains"  # String contains
    EXISTS = "exists"   # Key exists


class FilterCondition:
    """A single filter condition."""

    def __init__(self, field: str, operator: FilterOperator, value: Any = None):
        """Initialize a filter condition.

        Args:
            field: Metadata field name.
            operator: Comparison operator.
            value: Value to compare against.
        """
        self.field = field
        self.operator = operator
        self.value = value

    def match(self, metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches this condition.

        Args:
            metadata: Metadata dictionary to check.

        Returns:
            True if metadata matches the condition.
        """
        if self.operator == FilterOperator.EXISTS:
            return self.field in metadata

        if self.field not in metadata:
            return False

        val = metadata[self.field]

        if self.operator == FilterOperator.EQ:
            return val == self.value
        elif self.operator == FilterOperator.NEQ:
            return val != self.value
        elif self.operator == FilterOperator.GT:
            return val > self.value
        elif self.operator == FilterOperator.GTE:
            return val >= self.value
        elif self.operator == FilterOperator.LT:
            return val < self.value
        elif self.operator == FilterOperator.LTE:
            return val <= self.value
        elif self.operator == FilterOperator.IN:
            return val in self.value
        elif self.operator == FilterOperator.NIN:
            return val not in self.value
        elif self.operator == FilterOperator.CONTAINS:
            return self.value in str(val)
        return False


class MetadataFilter:
    """Metadata filter with AND/OR logic."""

    def __init__(self):
        """Initialize an empty filter."""
        self.conditions: List[FilterCondition] = []
        self.logic = "and"  # "and" or "or"

    def add_condition(self, field: str, operator: Union[FilterOperator, str],
                      value: Any = None) -> "MetadataFilter":
        """Add a filter condition.

        Args:
            field: Metadata field name.
            operator: Comparison operator (FilterOperator or string).
            value: Value to compare against.

        Returns:
            Self for chaining.
        """
        if isinstance(operator, str):
            operator = FilterOperator(operator)
        self.conditions.append(FilterCondition(field, operator, value))
        return self

    def set_logic(self, logic: str) -> "MetadataFilter":
        """Set the logic for combining conditions.

        Args:
            logic: "and" or "or".

        Returns:
            Self for chaining.
        """
        if logic not in ("and", "or"):
            raise ValueError("Logic must be 'and' or 'or'")
        self.logic = logic
        return self

    def match(self, metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches all conditions.

        Args:
            metadata: Metadata dictionary to check.

        Returns:
            True if metadata matches the filter.
        """
        if not self.conditions:
            return True

        if self.logic == "and":
            return all(c.match(metadata) for c in self.conditions)
        else:
            return any(c.match(metadata) for c in self.conditions)


def eq(field: str, value: Any) -> MetadataFilter:
    """Create an equality filter."""
    f = MetadataFilter()
    f.add_condition(field, FilterOperator.EQ, value)
    return f


def gt(field: str, value: Any) -> MetadataFilter:
    """Create a greater-than filter."""
    f = MetadataFilter()
    f.add_condition(field, FilterOperator.GT, value)
    return f


def gte(field: str, value: Any) -> MetadataFilter:
    """Create a greater-than-or-equal filter."""
    f = MetadataFilter()
    f.add_condition(field, FilterOperator.GTE, value)
    return f


def lt(field: str, value: Any) -> MetadataFilter:
    """Create a less-than filter."""
    f = MetadataFilter()
    f.add_condition(field, FilterOperator.LT, value)
    return f


def lte(field: str, value: Any) -> MetadataFilter:
    """Create a less-than-or-equal filter."""
    f = MetadataFilter()
    f.add_condition(field, FilterOperator.LTE, value)
    return f


def range_filter(field: str, min_val: Any, max_val: Any) -> MetadataFilter:
    """Create a range filter (min <= value <= max).

    Args:
        field: Metadata field name.
        min_val: Minimum value (inclusive).
        max_val: Maximum value (inclusive).

    Returns:
        MetadataFilter with range conditions.
    """
    f = MetadataFilter()
    f.add_condition(field, FilterOperator.GTE, min_val)
    f.add_condition(field, FilterOperator.LTE, max_val)
    return f
