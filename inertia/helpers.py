from typing import Any, Type, TypeVar

T = TypeVar("T")


def deep_transform_callables(prop: Any) -> Any:
    """Recursively transform callables in a dictionary into their return values"""
    if not isinstance(prop, dict):
        return prop() if callable(prop) else prop

    for key in list(prop.keys()):
        prop[key] = deep_transform_callables(prop[key])

    return prop


def validate_type(value: Any, name: str, expected_type: Type[T]) -> T:
    """Validate that a value is of the expected type"""
    if not isinstance(value, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__} for {name}, got {type(value).__name__}"
        )

    return value
