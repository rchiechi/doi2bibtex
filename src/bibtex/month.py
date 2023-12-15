import abc
from collections import OrderedDict
from typing import Tuple, Union

from bibtexparser.library import Library
from bibtexparser.model import Block, Entry, Field

from bibtexparser.middlewares.middleware import BlockMiddleware


class _MonthInterpolator(BlockMiddleware, abc.ABC):
    """Abstract class to handle month-conversions."""

    # docstr-coverage: inherited
    def __init__(self, allow_inplace_modification: bool):
        super().__init__(
            allow_inplace_modification=allow_inplace_modification,
            allow_parallel_execution=True,
        )

    # docstr-coverage: inherited
    def transform_entry(self, entry: Entry, library: "Library") -> Block:
        try:
            month = entry.fields_dict["month"]
        except KeyError:
            return entry

        new_val, meta = self.resolve_month_field_val(month)
        month.value = new_val
        entry.parser_metadata[self.metadata_key()] = meta
        return entry

    @abc.abstractmethod
    def resolve_month_field_val(
        self, month_field: Field
    ) -> Tuple[Union[str, int], str]:
        """Transform the month field.

        Args:
            month_field: The month field to transform.

        Returns:
            A tuple of the transformed value and the metadata."""
        raise NotImplementedError("Abstract method")


_MONTH_ABBREV_TO_FULL = OrderedDict(
    [
        ("jan", "January"),
        ("feb", "February"),
        ("mar", "March"),
        ("apr", "April"),
        ("may", "May"),
        ("jun", "June"),
        ("jul", "July"),
        ("aug", "August"),
        ("sep", "September"),
        ("oct", "October"),
        ("nov", "November"),
        ("dec", "December"),
    ]
)

_MONTH_ABBREV = list(_MONTH_ABBREV_TO_FULL.keys())

_MONTH_FULL = list(_MONTH_ABBREV_TO_FULL.values())

_LOWERCASE_FULL = list(m.lower() for m in _MONTH_FULL)


class MonthIntStrMiddleware(_MonthInterpolator):
    """Replace month values with month numbers.

    https://github.com/sciunto-org/python-bibtexparser/blob/main/bibtexparser/middlewares/month.py
    The original returns int values that break latex decoding.

    Note that this may be used before or after removing the enclosing,
    but the semantics are different: Enclosed values (e.g. '{jan}', '"jan"' or '"1"')
    will not be transformed. If you want to transform these values, you should
    use this middleware after the RemoveEnclosingMiddleware.

    The created int-months are always integers and unenclosed."""

    # docstr-coverage: inherited
    @staticmethod
    def metadata_key() -> str:
        return "MonthIntMiddleware"

    # docstr-coverage: inherited
    def resolve_month_field_val(self, month_field: Field):
        v = month_field.value
        if isinstance(v, str):
            v_lower = v.lower()
            if v_lower in _MONTH_ABBREV:
                return (
                    str(_MONTH_ABBREV.index(v_lower[:3]) + 1),
                    "transformed full month to int-month",
                )
            elif v_lower in _LOWERCASE_FULL:
                return (
                    str(_LOWERCASE_FULL.index(v_lower) + 1),
                    "transformed abbreviated month to int-month",
                )

        if isinstance(v, str) and v.isdigit():
            if 1 <= int(v) <= 12:
                return v, "cast month int-string to str"

        return month_field.value, "month field unchanged"