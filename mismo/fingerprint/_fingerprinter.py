from __future__ import annotations

from typing import Callable, Protocol, Sequence, Union

import ibis
from ibis.expr.types import ArrayColumn, Column, Table

from mismo._dataset import PDataset


class PFingerprinter(Protocol):
    def fingerprint(self, data: PDataset) -> ArrayColumn:
        ...

    @property
    def name(self) -> str:
        ...


def is_fingerprinter(fp):
    return hasattr(fp, "fingerprint") and callable(fp.fingerprint)


FingerprintFunction = Callable[[PDataset], ArrayColumn]
Columns = Union[str, Sequence[str], None]


class MultiColumnFingerprinter(PFingerprinter):
    columns: str | list[str] | None

    def __init__(self, columns: Columns = None) -> None:
        if columns is None:
            self.columns = columns
        elif isinstance(columns, str):
            self.columns = [columns]
        else:
            cols = list(columns)
            if not all(isinstance(c, str) for c in cols):
                raise ValueError("Columns must be strings")
            self.columns = cols

    def _select_columns(self, data: Table) -> Table:
        if self.columns is None:
            return data
        else:
            return data[self.columns]  # type: ignore

    def _func(self, subset: Table) -> ArrayColumn:
        raise NotImplementedError()

    def fingerprint(self, data: PDataset) -> ArrayColumn:
        subset = self._select_columns(data.table)
        return self._func(subset).name(self.name)  # type: ignore


class SingleColumnFingerprinter(PFingerprinter):
    def __init__(self, column: str) -> None:
        if not isinstance(column, str):
            raise ValueError("column must be a string")
        self.column = column

    def _func(self, col: Column) -> ArrayColumn:
        raise NotImplementedError()

    def fingerprint(self, data: PDataset) -> ArrayColumn:
        column = data.table[self.column]
        return self._func(column).name(self.name)  # type: ignore


class FunctionFingerprinter(PFingerprinter):
    def __init__(self, func: FingerprintFunction) -> None:
        self.func = func

    @property
    def name(self) -> str:
        try:
            func_name = self.func.__name__
        except AttributeError:
            func_name = "lambda"
        return func_name

    def fingerprint(self, data: PDataset) -> ArrayColumn:
        return self.func(data)


class Equals(SingleColumnFingerprinter):
    def _func(self, col: Column) -> ArrayColumn:
        return ibis.array([col], type=col.type())  # type: ignore

    @property
    def name(self) -> str:
        return f"equals_{self.column}"