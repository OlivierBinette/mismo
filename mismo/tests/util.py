from __future__ import annotations

from ibis.expr import types as it
import pandas._testing as tm


def assert_tables_equal(left: it.Table, right: it.Table) -> None:
    assert left.schema() == right.schema()
    left_df = left.order_by(left.columns).to_pandas()
    right_df = right.order_by(left.columns).to_pandas()
    try:
        tm.assert_frame_equal(left_df, right_df)
    except AssertionError:
        print(left_df)
        print(right_df)
        raise
