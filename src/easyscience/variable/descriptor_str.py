# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from .descriptor_base import DescriptorBase


class DescriptorStr(DescriptorBase):
    """A ``Descriptor`` for string values."""

    def __init__(
        self,
        value: str,
        *,
        unique_name: str | None = None,
        description: str | None = None,
        url: str | None = None,
        display_name: str | None = None,
    ):
        """
        Constructor for the DescriptorStr class.

        All arguments after ``value`` are keyword-only.

        Parameters
        ----------
        value : str
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
            If ``value`` is not a string.
        """
        super().__init__(
            unique_name=unique_name,
            description=description,
            url=url,
            display_name=display_name,
        )
        if not isinstance(value, str):
            raise ValueError(f'{value=} must be type str')
        self._string = value

    @property
    def value(self) -> str:
        """
        Get the value of self.

        Returns
        -------
        str
            Value of self with unit.
        """
        return self._string

    @value.setter
    def value(self, value: str) -> None:
        """
        Set the value of self.

        Parameters
        ----------
        value : str
            New value of self.

        Returns
        -------
        None
            None.

        Raises
        ------
        ValueError
            If ``value`` is not a string.
        """
        if not isinstance(value, str):
            raise ValueError(f'{value=} must be type str')
        self._string = value

    def __repr__(self) -> str:
        """Return printable representation."""
        class_name = self.__class__.__name__
        obj_name = self.display_name
        obj_value = self._string
        return f"<{class_name} '{obj_name}': {obj_value}>"

    # To get return type right
    def __copy__(self) -> DescriptorStr:
        return super().__copy__()
