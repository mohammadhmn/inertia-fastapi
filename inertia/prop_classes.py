"""
Inertia.js property classes for FastAPI.

This module provides special property classes that modify how props
are handled by Inertia, such as deferred loading, merging, and ignoring
on first load.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Union


class CallableProp:
    """Base class for props that can be callables.

    This wraps a value or callable and handles calling it when needed.
    """

    def __init__(self, prop: Union[Callable[[], Any], Any]):
        """Initialize with a value or callable.

        Args:
            prop: A value or callable that returns a value
        """
        self.prop = prop

    def __call__(self) -> Any:
        """Call the prop if it's callable, otherwise return it directly.

        Returns:
            The value of the prop
        """
        return self.prop() if callable(self.prop) else self.prop


class MergeableProp(ABC):
    """Abstract base class for props that can be merged.

    Mergeable props can update existing JavaScript values rather than
    replacing them entirely.
    """

    @abstractmethod
    def should_merge(self) -> bool:
        """Determine if this prop should be merged.

        Returns:
            True if the prop should be merged, False otherwise
        """
        pass


class IgnoreOnFirstLoadProp:
    """Marker class for props that should be ignored on first page load.

    These props will only be included in partial reloads (when the page
    is already loaded) and not on the initial page load.
    """

    pass


class OptionalProp(CallableProp, IgnoreOnFirstLoadProp):
    """Prop that is only included in partial reloads.

    This is useful for data that is expensive to compute and not needed
    for the initial page load.
    """

    pass


class DeferredProp(CallableProp, MergeableProp, IgnoreOnFirstLoadProp):
    """Prop that is deferred for lazy loading and can be merged.

    This allows for expensive data to be loaded after the initial page load
    and can optionally be merged with existing data.
    """

    def __init__(
        self,
        prop: Union[Callable[[], Any], Any],
        group: str = "default",
        merge: bool = False,
    ):
        """Initialize a deferred prop.

        Args:
            prop: The value or callable that returns the value
            group: The group this prop belongs to for lazy loading
            merge: Whether to merge this prop with existing data
        """
        super().__init__(prop)
        self.group = group
        self.merge = merge

    def should_merge(self) -> bool:
        """Determine if this prop should be merged.

        Returns:
            True if merge is enabled, False otherwise
        """
        return self.merge


class MergeProp(CallableProp, MergeableProp):
    """Prop that is always merged with existing data.

    This is useful for updates that should modify rather than replace
    existing JavaScript objects.
    """

    def should_merge(self) -> bool:
        """Always returns True as this prop should always be merged.

        Returns:
            True
        """
        return True
