# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from .descriptor_base import DescriptorBase


class DescriptorBool(DescriptorBase):
    """A ``Descriptor`` for boolean values."""

    def __init__(
        self,
        value: bool,
        *,
        unique_name: str | None = None,
        description: str | None = None,
        url: str | None = None,
        display_name: str | None = None,
    ):
        """
        Constructor for the DescriptorBool class.

        All arguments after ``value`` are keyword-only.

        Parameters
        ----------
        value : bool
            Value of this object.
        unique_name : str | None, default=None
            Unique identifier for this object. By default, None.
        description : str | None, default=None
            A brief summary of what this object is. By default, None.
        url : str | None, default=None
            Lookup url for documentation/information. By default, None.
        display_name : str | None, default=None
            A pretty name for the object. Falls back to ``unique_name``
            when not given. By default, None.

        Raises
        ------
        ValueError
            If ``value`` is not a boolean.
        """
        if not isinstance(value, bool):
            raise ValueError(f'{value=} must be type bool')
        super().__init__(
            unique_name=unique_name,
            description=description,
            url=url,
            display_name=display_name,
        )
        self._bool_value = value

    @property
    def value(self) -> bool:
        """
        Get the value of self.

        Returns
        -------
        bool
            Value of self.
        """
        return self._bool_value

    @value.setter
    def value(self, value: bool) -> None:
        """
        Set the value of self.

        Parameters
        ----------
        value : bool
            New value of self.

        Returns
        -------
        None
            None.

        Raises
        ------
        TypeError
            If ``value`` is not a boolean.
        """
        if not isinstance(value, bool):
            raise TypeError(f'{value=} must be type bool')
        self._bool_value = value

    def __repr__(self) -> str:
        """Return printable representation."""
        class_name = self.__class__.__name__
        obj_name = self.display_name
        obj_value = self._bool_value
        return f"<{class_name} '{obj_name}': {obj_value}>"

    # To get return type right
    def __copy__(self) -> DescriptorBool:
        return super().__copy__()
